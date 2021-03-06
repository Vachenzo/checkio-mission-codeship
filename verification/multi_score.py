from checkio.referees.multicall import CheckiORefereeMulti
from checkio import api
from checkio.signals import PROCESS_ENDED

REQ = 'req'
REFEREE = 'referee'

class CheckiORefereeMultiScore(CheckiORefereeMulti):
    def __init__(self, *args, **kwargs):
        self.total_score = 0
        super().__init__(*args, **kwargs)

    def on_ready(self, data):
        self.code = data['code']
        self.runner = data['runner']
        if self.inspector:
            result, result_message = self.inspector(self.code, self.runner)
            if not result:
                api.fail(0, result_message)
        self.seed = data.get("seed", "checkio")
        self.start_env()

        api.add_process_listener(REQ, PROCESS_ENDED, self.process_req_ended)

    def check_current_test(self, data):
        user_result = data['result']
        if isinstance(user_result, str):
            self.seed += user_result
        self.referee_data = self.process_referee(self.referee_data, user_result, self.seed)

        self.total_score += self.referee_data.get("score", 0)

        referee_result = self.referee_data.get("result", False)

        if referee_result and self.is_win_referee:
            is_win_result = self.is_win_referee(self.referee_data)
        else:
            is_win_result = self.referee_data.get("is_win", False)

        self.referee_data.update({"is_win": is_win_result})

        api.request_write_ext(self.referee_data)

        if not referee_result:
            if self.total_score:
                return api.success(score=self.total_score)
            else:
                return api.fail(self.current_step, self.get_current_test_fullname())

        if not is_win_result:
            self.test_current_step()
        else:
            self.total_score += self.referee_data["fuel"]
            if self.next_env():
                self.restart_env()
            else:
                api.success(score=self.total_score)