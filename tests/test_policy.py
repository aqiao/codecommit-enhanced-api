from source.policy import load_policy_template


class TestPolicy(object):

    def test_load_policy_template(self):
        policy_type = 'developer'
        load_policy_template(policy_type)