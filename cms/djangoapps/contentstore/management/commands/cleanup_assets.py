"""
Script for removing all redundant Mac OS metadata files (with filename ".DS_Store"
or with filename which starts with "._") for all courses
"""
from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore


class Command(BaseCommand):
    """
    Remove all Mac OS related redundant files for all courses in mongo
    """
    help = 'Remove all Mac OS related redundant file/files for all courses in mongo'

    def handle(self, *args, **options):
        """
        Execute the command
        """
        content_store = contentstore()
        module_store = modulestore()
        courses = module_store.get_courses()

        course_ids = [x.id for x in courses]
        cleanup_failed_courses = []

        for course_id in course_ids:

            print(u"-" * 80)
            print(u"Cleaning up assets for course id = {0}".format(course_id))

            try:
                # Remove all redundant Mac OS metadata files
                content_store.remove_redundant_content_for_course(course_id)
            except Exception as err:
                cleanup_failed_courses.append(unicode(course_id))
                print(u"=" * 30 + u"> failed to cleanup %s" % course_id)
                print(u"Error:")
                print(err)

        print(u"=" * 80)
        print(u"=" * 30 + u"> Assets cleanup summary")
        print(u"Total number of courses for assets cleanup: {0}".format(len(courses)))
        print(u"Total number of courses which failed for assets cleanup: {0}".format(len(cleanup_failed_courses)))
        print(u"List of assets cleanup failed courses ids: {0}".format(cleanup_failed_courses))
