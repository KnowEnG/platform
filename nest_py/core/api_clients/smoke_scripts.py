#Utilities for running smoke_tests against the REST API

class SmokeTestResult():
    """
    Simple log accumulator that can be passed along
    through a smoke test so that the final report
    can be printed in full in case of a problem.
    """

    def __init__(self, script_name):
        """
        script_name(String) for logging
        """
        self.succeeded = True
        self.full_report = 'SmokeTest: ' + script_name + '\n'

    def set_success(self, did_succeed):
        if not did_succeed:
            print("Declaring FAILURE")
        self.succeeded = did_succeed

    def did_succeed(self):
        return self.succeeded

    def add_report_line(self, line_str):
        print(line_str)
        self.full_report += line_str + '\n'
        return

    def get_full_report(self):
        return self.full_report

def login_client(http_client, result_acc):
    """
    logs into the http client as a default user during a smoke_test. If it
    fails, sets the result_acc to failure with a log message.  The http_client
    will have it's internal jwt_token set for the remainder of it's life.
    
    http_client(NestHttpClient)
    result_acc(SmokeTestResult)
    """
    try:
        http_client.login('fakeuser', 'GARBAGESECRET')
    except Exception as ex:
        result_acc.set_success(False)
        result_acc.add_report_line(
            "smoke_scripts couldn't login as the default jobs user")
        print(str(ex))
    return 
