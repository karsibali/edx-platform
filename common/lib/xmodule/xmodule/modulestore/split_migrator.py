'''
Code for migrating from other modulestores to the split_mongo modulestore.

Exists at the top level of modulestore b/c it needs to know about and access each modulestore.

In general, it's strategy is to treat the other modulestores as read-only and to never directly
manipulate storage but use existing api's.
'''
import logging

from xblock.fields import Reference, ReferenceList, ReferenceValueDict
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.locator import CourseLocator

log = logging.getLogger(__name__)


class SplitMigrator(object):
    """
    Copies courses from old mongo to split mongo and sets up location mapping so any references to the old
    name will be able to find the new elements.
    """
    def __init__(self, split_modulestore, source_modulestore):
        super(SplitMigrator, self).__init__()
        self.split_modulestore = split_modulestore
        self.source_modulestore = source_modulestore

    def migrate_mongo_course(self, source_course_key, user_id, new_org=None, new_course=None, new_run=None):
        """
        Create a new course in split_mongo representing the published and draft versions of the course from the
        original mongo store. And return the new CourseLocator

        If the new course already exists, this raises DuplicateItemError

        :param source_course_key: which course to migrate
        :param user_id: the user whose action is causing this migration
        :param new_org, new_course, new_run: (optional) identifiers for the new course. Defaults to
            the source_course_key's values.
        """
        # the only difference in data between the old and split_mongo xblocks are the locations;
        # so, any field which holds a location must change to a Locator; otherwise, the persistence
        # layer and kvs's know how to store it.
        # locations are in location, children, conditionals, course.tab

        # create the course: set fields to explicitly_set for each scope, id_root = new_course_locator, master_branch = 'production'
        original_course = self.source_modulestore.get_course(source_course_key)

        if new_org is None:
            new_org = source_course_key.org
        if new_course is None:
            new_course = source_course_key.course
        if new_run is None:
            new_run = source_course_key.run
        new_course_key = CourseLocator(new_org, new_course, new_run, branch=ModuleStoreEnum.BranchName.published)
        new_course = self.split_modulestore.create_course(
            new_org, new_course, new_run, user_id,
            fields=self._get_json_fields_translate_references(original_course, new_course_key, None),
            master_branch=ModuleStoreEnum.BranchName.published,
        )

        with self.split_modulestore.bulk_write_operations(new_course.id):
            self._copy_published_modules_to_course(new_course, original_course.location, source_course_key, user_id)
        # create a new version for the drafts
        with self.split_modulestore.bulk_write_operations(new_course.id):
            self._add_draft_modules_to_course(new_course.location, source_course_key, user_id)

        return new_course.id

    def _copy_published_modules_to_course(self, new_course, old_course_loc, source_course_key, user_id):
        """
        Copy all of the modules from the 'direct' version of the course to the new split course.
        """
        course_version_locator = new_course.id

        # iterate over published course elements. Wildcarding rather than descending b/c some elements are orphaned (e.g.,
        # course about pages, conditionals)
        for module in self.source_modulestore.get_items(
            source_course_key, revision=ModuleStoreEnum.RevisionOption.published_only
        ):
            # don't copy the course again.
            if module.location != old_course_loc:
                # create split_xblock using split.create_item
                # NOTE: the below auto populates the children when it migrates the parent; so,
                # it doesn't need the parent as the first arg. That is, it translates and populates
                # the 'children' field as it goes.
                _new_module = self.split_modulestore.create_item(
                    course_version_locator, module.category, user_id,
                    block_id=module.location.block_id,
                    fields=self._get_json_fields_translate_references(
                        module, course_version_locator, new_course.location.block_id
                    ),
                    # TODO remove continue_version when bulk write is impl'd
                    continue_version=True
                )
        # after done w/ published items, add version for DRAFT pointing to the published structure
        index_info = self.split_modulestore.get_course_index_info(course_version_locator)
        versions = index_info['versions']
        versions[ModuleStoreEnum.BranchName.draft] = versions[ModuleStoreEnum.BranchName.published]
        self.split_modulestore.update_course_index(index_info)

        # clean up orphans in published version: in old mongo, parents pointed to the union of their published and draft
        # children which meant some pointers were to non-existent locations in 'direct'
        self.split_modulestore.internal_clean_children(course_version_locator)

    def _add_draft_modules_to_course(self, published_course_usage_key, source_course_key, user_id):
        """
        update each draft. Create any which don't exist in published and attach to their parents.
        """
        # each true update below will trigger a new version of the structure. We may want to just have one new version
        # but that's for a later date.
        new_draft_course_loc = published_course_usage_key.course_key.for_branch(ModuleStoreEnum.BranchName.draft)
        # to prevent race conditions of grandchilden being added before their parents and thus having no parent to
        # add to
        awaiting_adoption = {}
        for module in self.source_modulestore.get_items(source_course_key, revision=ModuleStoreEnum.RevisionOption.draft_only):
            new_locator = new_draft_course_loc.make_usage_key(module.category, module.location.block_id)
            if self.split_modulestore.has_item(new_locator):
                # was in 'direct' so draft is a new version
                split_module = self.split_modulestore.get_item(new_locator)
                # need to remove any no-longer-explicitly-set values and add/update any now set values.
                for name, field in split_module.fields.iteritems():
                    if field.is_set_on(split_module) and not module.fields[name].is_set_on(module):
                        field.delete_from(split_module)
                for field, value in self._get_fields_translate_references(
                        module, new_draft_course_loc, published_course_usage_key.block_id
                ).iteritems():
                    field.write_to(split_module, value)

                _new_module = self.split_modulestore.update_item(split_module, user_id)
            else:
                # only a draft version (aka, 'private').
                _new_module = self.split_modulestore.create_item(
                    new_draft_course_loc, module.category, user_id,
                    block_id=new_locator.block_id,
                    fields=self._get_json_fields_translate_references(
                        module, new_draft_course_loc, published_course_usage_key.block_id
                    )
                )
                awaiting_adoption[module.location] = new_locator
        for draft_location, new_locator in awaiting_adoption.iteritems():
            parent_loc = self.source_modulestore.get_parent_location(
                draft_location, revision=ModuleStoreEnum.RevisionOption.draft_preferred
            )
            if parent_loc is None:
                log.warn(u'No parent found in source course for %s', draft_location)
                continue
            old_parent = self.source_modulestore.get_item(parent_loc)
            split_parent_loc = new_draft_course_loc.make_usage_key(
                parent_loc.category,
                parent_loc.block_id if parent_loc.category != 'course' else published_course_usage_key.block_id
            )
            new_parent = self.split_modulestore.get_item(split_parent_loc)
            # this only occurs if the parent was also awaiting adoption: skip this one, go to next
            if any(new_locator == child.version_agnostic() for child in new_parent.children):
                continue
            # find index for module: new_parent may be missing quite a few of old_parent's children
            new_parent_cursor = 0
            for old_child_loc in old_parent.children:
                if old_child_loc == draft_location:
                    break  # moved cursor enough, insert it here
                sibling_loc = new_draft_course_loc.make_usage_key(old_child_loc.category, old_child_loc.block_id)
                # sibling may move cursor
                for idx in range(new_parent_cursor, len(new_parent.children)):
                    if new_parent.children[idx].version_agnostic() == sibling_loc:
                        new_parent_cursor = idx + 1
                        break  # skipped sibs enough, pick back up scan
            new_parent.children.insert(new_parent_cursor, new_locator)
            new_parent = self.split_modulestore.update_item(new_parent, user_id)

    def _get_json_fields_translate_references(self, xblock, new_course_key, course_block_id):
        """
        Return the json repr for explicitly set fields but convert all references to their Locators
        """
        def get_translation(location):
            """
            Convert the location
            """
            return new_course_key.make_usage_key(
                location.category,
                location.block_id if location.category != 'course' else course_block_id
            )

        result = {}
        for field_name, field in xblock.fields.iteritems():
            if field.is_set_on(xblock):
                field_value = getattr(xblock, field_name)
                if isinstance(field, Reference) and field_value is not None:
                    result[field_name] = get_translation(field_value)
                elif isinstance(field, ReferenceList):
                    result[field_name] = [
                        get_translation(ele) for ele in field_value
                    ]
                elif isinstance(field, ReferenceValueDict):
                    result[field_name] = {
                        key: get_translation(subvalue)
                        for key, subvalue in field_value.iteritems()
                    }
                else:
                    result[field_name] = field.read_json(xblock)

        return result

    def _get_fields_translate_references(self, xblock, new_course_key, course_block_id):
        """
        Return a dictionary of field: value pairs for explicitly set fields
        but convert all references to their BlockUsageLocators
        """
        def get_translation(location):
            """
            Convert the location
            """
            return new_course_key.make_usage_key(
                location.category,
                location.block_id if location.category != 'course' else course_block_id
            )

        result = {}
        for field_name, field in xblock.fields.iteritems():
            if field.is_set_on(xblock):
                field_value = getattr(xblock, field_name)
                if isinstance(field, Reference) and field_value is not None:
                    result[field] = get_translation(field_value)
                elif isinstance(field, ReferenceList):
                    result[field] = [
                        get_translation(ele) for ele in field_value
                    ]
                elif isinstance(field, ReferenceValueDict):
                    result[field] = {
                        key: get_translation(subvalue)
                        for key, subvalue in field_value.iteritems()
                    }
                else:
                    result[field] = field_value

        return result
