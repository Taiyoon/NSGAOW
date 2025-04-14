import unittest
from unittest.mock import patch
from simenv.submitter import SubmitterHybridDefault
from simenv.utils.traits import Runnable
from simenv.world import WorldHybrid


class TestTaskSubmitterHybridDefault(unittest.TestCase):

    def setUp(self) -> None:
        self.world = WorldHybrid({'stdout'})
        self.active_time = 10
        self.arrival_rate = 0.1
        self.task_submitter = self.world.task_submitter

    # def test_run_submits_task_to_world(self) -> None:
    #     with patch.object(self.task_submitter.world, 'submit_task') as mock_submit_task:
    #         with patch.object(self.task_submitter.env, 'timeout') as mock_timeout:
    #             mock_timeout.return_value = 'timeout'
    #             with patch.object(self.task_submitter, 'now') as mock_now:
    #                 mock_now.side_effect = [0, 1, 2, self.active_time]
    #                 self.task_submitter.run()
    #                 mock_submit_task.assert_called_with('timeout')


if __name__ == '__main__':
    unittest.main()
