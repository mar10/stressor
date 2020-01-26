# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from textwrap import dedent


class TestScripts:
    def setup_method(self):
        self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")

    def test_script(self):
        # config_path = os.path.join(self.fixtures_path, "test_mock_server.yaml")
        # rm = RunManager()
        # rm.load_config(config_path)
        # assert rm.run_config
        # assert rm.config_manager.file_version == 0
        # res = rm.run()
        # assert res is True
        script = """
        print("SCRIPT: globals()", globals())
        print("SCRIPT: globals()", globals()["foo"])
        print("SCRIPT:", globals()["foo"])
        # print("Hello world!", locals()[42])
        print("Hello world!", local)
        # print("Script globsals()!", globals())
        b = 18
        17
        """

        # TODO: Compile?

        # local_vars = locals()
        global_vars = {
            "foo": 41,
            # "__builtins__": {},
        }
        local_vars = {
            "local": 42,
        }
        res = exec(
            dedent(script),
            global_vars,
            # {
            #     # "__builtins__": None,
            #     "foo": "bar",
            # },
            {"local": 42},
        )
        print("Result: {}".format(res))
        # print("Globals: {}".format(global_vars))
        print("Locals: {}".format(local_vars))
        # assert 0
