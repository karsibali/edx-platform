import json
import mock
from contentstore.views.course import GroupConfiguration
from contentstore.utils import reverse_course_url
from contentstore.tests.utils import CourseTestCase
from xmodule.partitions.partitions import UserPartition
from xmodule.modulestore.tests.factories import ItemFactory


class GroupConfigurationsCreateTestCase(CourseTestCase):
    """
    Test cases for creating a new group configurations.
    """

    def setUp(self):
        """
        Set up a url and group configuration content for tests.
        """
        super(GroupConfigurationsCreateTestCase, self).setUp()
        self.url = reverse_course_url('group_configurations_list_handler', self.course.id)
        self.group_configuration_json = {
            u'description': u'Test description',
            u'name': u'Test name'
        }
        patcher = mock.patch('uuid.uuid1', return_value='test_id')
        self.patched_uuid = patcher.start()
        self.addCleanup(patcher.stop)

    def test_index_page(self):
        """
        Check that the group configuration index page responds correctly.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('New Group Configuration', response.content)

    def test_bad_http_accept_header(self):
        """
        Test if not allowed header present in request.
        """
        response = self.client.get(
            self.url,
            HTTP_ACCEPT="text/plain",
        )
        self.assertEqual(response.status_code, 406)

    def test_list_page_ajax(self):
        """
        Check that the group configuration lists all configurations.
        """
        group_configurations = [
            {
                u'description': u'Test description',
                u'id': 1,
                u'name': u'Test name',
                u'version': 1,
                u'groups': [
                    {u'id': 0, u'name': u'Group A', u'version': 1},
                    {u'id': 1, u'name': u'Group B', u'version': 1}
                ]
            },
            {
                u'description': u'Test description 2',
                u'id': 2,
                u'name': u'Test name 2',
                u'version': 1,
                u'groups': [
                    {u'id': 0, u'name': u'Group A', u'version': 1},
                    {u'id': 1, u'name': u'Group B', u'version': 1}
                ]
            }
        ]
        self.course.user_partitions = [
            UserPartition.from_json(configuration)
            for configuration in group_configurations
        ]
        self.save_course()
        response = self.client.get(
            self.url,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        group_configurations = json.loads(response.content)
        expected_group_configurations = [
            {
                u'description': u'Test description',
                u'id': 1,
                u'name': u'Test name',
                u'groups': [
                    {u'id': 0, u'name': u'Group A'},
                    {u'id': 1, u'name': u'Group B'}
                ]
            },
            {
                u'description': u'Test description 2',
                u'id': 2,
                u'name': u'Test name 2',
                u'groups': [
                    {u'id': 0, u'name': u'Group A'},
                    {u'id': 1, u'name': u'Group B'}
                ]
            },
        ]
        self.assertItemsEqual(group_configurations, expected_group_configurations)

    def test_group_success(self):
        """
        Test that you can create a group configuration.
        """
        expected_group_configuration = {
            u'id': u'test_id',
            u'description': u'Test description',
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(self.group_configuration_json),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        group_configuration = json.loads(response.content)
        self.assertEqual(expected_group_configuration, group_configuration)

    def test_bad_group(self):
        """
        Test if only one group in configuration exist.
        """
        # Only one group in group configuration here.
        bad_group_configuration = {
            u'description': u'Test description',
            u'id': 1,
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
            ]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(bad_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)

    def test_bad_json(self):
        """
        Test bad json handling.
        """
        bad_jsons = [
            {u'name': 'Test Name'},
            {u'description': 'Test description'},
            {}
        ]
        for bad_json in bad_jsons:
            response = self.client.post(
                self.url,
                data=json.dumps(bad_json),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("Location", response)
            content = json.loads(response.content)
            self.assertIn("error", content)

    def test_invalid_json(self):
        """
        Test invalid json handling.
        """
        # No property name.
        invalid_json = "{u'name': 'Test Name', []}"

        response = self.client.post(
            self.url,
            data=invalid_json,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)


class GroupConfigurationsDetailTestCase(CourseTestCase):
    """
    Test cases for detail handler.
    """

    def setUp(self):
        """
        Set up a url and group configuration content for tests.
        """
        super(GroupConfigurationsDetailTestCase, self).setUp()

        self.group_configuration_json = {
            u'description': u'Test description',
            u'name': u'Test name'
        }

        self.test_id = u'0e11749e-0682-11e4-9247-080027880ca6'
        self.group_configuration = {
            u'description': u'Test description',
            u'id': self.test_id,
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }
        self._set_user_partition(self.group_configuration)

    def _set_user_partition(self, group_configuration):
        self.course.user_partitions = [UserPartition.from_json(group_configuration)]
        self.save_course()

    def test_group_configuration_new(self):
        """
        PUT group configuration when no configurations exist in course.
        """
        # Make no partitions in course.
        self.course.user_partitions = []
        self.save_course()

        edit_group_configuration = {
            u'description': u'Edit Test description',
            u'id': self.test_id,
            u'name': u'Edit Test name',
            u'groups': [
                {u'name': u'Group A'},
                {u'name': u'Group B'}
            ]
        }
        put_url = reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': self.test_id}
        )
        response = self.client.put(
            put_url,
            data=json.dumps(edit_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content['id'], self.test_id)
        self.assertEqual(content['description'], 'Edit Test description')
        self.assertEqual(content['name'], 'Edit Test name')

    def test_group_configuration_edit(self):
        """
        Edit group configuration and check its id and modified fields.
        """
        edit_group_configuration = {
            u'description': u'Edit Test description',
            u'id': self.test_id,
            u'name': u'Edit Test name',
            u'groups': [
                {u'name': u'Group A'},
                {u'name': u'Group B'}
            ]
        }
        put_url = reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': self.test_id}
        )
        response = self.client.put(
            put_url,
            data=json.dumps(edit_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content['id'], self.test_id)
        self.assertEqual(content['description'], 'Edit Test description')
        self.assertEqual(content['name'], 'Edit Test name')

    def test_group_configuration_not_exists(self):
        """
        Group configuration is not present in course.
        """
        bad_id = u'bad-id'
        url = reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': bad_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_group_configuration_exists(self):
        """
        Group configuration with appropriate id is present in course.
        """
        url = reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': self.test_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        group_configuration = json.loads(response.content)
        expected_group_configuration = {
            u'description': u'Test description',
            u'id': self.test_id,
            u'name': u'Test name',
            u'groups': [
                {u'id': 0, u'name': u'Group A'},
                {u'id': 1, u'name': u'Group B'}
            ]
        }
        self.assertEqual(group_configuration, expected_group_configuration)

    def test_group_configuration_json_id_not_exists(self):
        """
        Attempt to edit nonexisting group configuration.
        """
        # Nonexisting id in cousre here in json.
        edit_group_configuration = {
            u'description': u'Edit Test description',
            u'id': u'non-existing-id',
            u'name': u'Edit Test name',
            u'groups': [
                {u'name': u'Group A'},
                {u'name': u'Group B'}
            ]
        }
        # Group configuration that present in course.
        put_url = reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': self.test_id}
        )
        response = self.client.put(
            put_url,
            data=json.dumps(edit_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content['id'], self.test_id)

    def test_update_bad_group(self):
        """
        Only one group in configuration exist on update.
        """
        # Only one group in group configuration here.
        bad_group_configuration = {
            u'description': u'Test description',
            u'id': self.test_id,
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
            ]
        }
        # Group configuration id that present in course.
        url = reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': self.test_id}
        )
        response = self.client.post(
            url,
            data=json.dumps(bad_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertIn("error", content)


class GroupConfigurationsUsageInfoTestCase(CourseTestCase):
    def setUp(self):
        """
        Set up group configurations and split test module.
        """
        super(GroupConfigurationsUsageInfoTestCase, self).setUp()

        self.group_configuration_id_1 = 123456789
        self.group_configuration_1 = {
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }

        self.group_configuration_id_2 = 987654321
        self.group_configuration_2 = {
            u'description': u'Test description 2',
            u'id': self.group_configuration_id_2,
            u'name': u'Group configuration name 2',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }
        self.course.user_partitions = [UserPartition.from_json(self.group_configuration_1)]

        self.vertical = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit 1'
        )
        self.split_test = ItemFactory.create(
            category='split_test',
            parent_location=self.vertical.location,
            user_partition_id=str(self.group_configuration_id_1),
            display_name='Test Content Experiment 1'
        )
        self.save_course()

    def test_group_configuration_used(self):
        """
        Test that right datastructure will be created when group configuration is used.
        """
        expected_usage_info = {
            self.group_configuration_id_1: [
                {
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                    'label': 'Test Unit 1 / Test Content Experiment 1'
                }
            ]
        }
        usage_info = GroupConfiguration._get_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        self.assertEqual(expected_usage_info, usage_info)

    def test_group_configuration_not_used(self):
        """
        Test that right datastructure will be created if group configuration is not used.
        """
        self.store.delete_item(self.split_test.location)
        expected_empty_dict = {}
        result = GroupConfiguration._get_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        self.assertEqual(expected_empty_dict, result)

    def test_usage_info_added(self):
        """
        Test if group configurations json updated successfully.
        """
        updated_configuration = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [{
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ],
            u'usage': [{
                'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                'label': 'Test Unit 1 / Test Content Experiment 1'
            }]
        }]
        self.assertEqual(expected, updated_configuration)

    def test_usage_info_no_experiment(self):
        """
        Test if group configurations json updated successfully if it not used in
        experiments.
        """
        self.store.delete_item(self.split_test.location)
        updated_configuration = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [{
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ],
            u'usage': []
        }]
        self.assertEqual(expected, updated_configuration)

    def test_one_configuration_in_multiple_experiments(self):
        """
        Test if multiple experiments are present in usage info when they use same
        group configuration.
        """
        self.vertical_2 = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit 2'
        )
        self.split_test_2 = ItemFactory.create(
            category='split_test',
            parent_location=self.vertical_2.location,
            user_partition_id=str(self.group_configuration_id_1),
            display_name='Test Content Experiment 2'
        )
        self.save_course()

        updated_configuration = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [{
            u'description': u'Test description 1',
            u'id': self.group_configuration_id_1,
            u'name': u'Group configuration name 1',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ],
            u'usage': [
                {
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                    'label': 'Test Unit 1 / Test Content Experiment 1'
                },
                {
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_2',
                    'label': 'Test Unit 2 / Test Content Experiment 2'
                },
            ]
        }]
        self.assertEqual(expected, updated_configuration)

    def test_two_configurations_two_experiments(self):
        """
        Test if multiple experiments are present in usage info when they use same
        group configuration.
        """
        self.course.user_partitions.append(UserPartition.from_json(self.group_configuration_2))
        self.vertical_2 = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit 2'
        )
        self.split_test_2 = ItemFactory.create(
            category='split_test',
            parent_location=self.vertical_2.location,
            user_partition_id=str(self.group_configuration_id_2),
            display_name='Test Content Experiment 2'
        )
        self.save_course()

        updated_configurations = GroupConfiguration.add_usage_info(
            self.course,
            self.store,
            self.course.location.course_key
        )
        expected = [
            {
                u'description': u'Test description 1',
                u'id': self.group_configuration_id_1,
                u'name': u'Group configuration name 1',
                u'version': 1,
                u'groups': [
                    {u'id': 0, u'name': u'Group A', u'version': 1},
                    {u'id': 1, u'name': u'Group B', u'version': 1}
                ],
                u'usage': [{
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_1',
                    'label': 'Test Unit 1 / Test Content Experiment 1'
                }]
            },
            {
                u'description': u'Test description 2',
                u'id': self.group_configuration_id_2,
                u'name': u'Group configuration name 2',
                u'version': 1,
                u'groups': [
                    {u'id': 0, u'name': u'Group A', u'version': 1},
                    {u'id': 1, u'name': u'Group B', u'version': 1}
                ],
                u'usage': [{
                    'url': '/unit/location:MITx+999+Robot_Super_Course+vertical+Test_Unit_2',
                    'label': 'Test Unit 2 / Test Content Experiment 2'
                }]
            }
        ]
        self.assertEqual(expected, updated_configurations)
