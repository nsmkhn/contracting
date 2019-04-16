import unittest
from seneca.execution.executor import Sandbox, Executor, MultiProcessingSandbox
import sys
import glob
# Import CRDriver and AbstractDatabaseDriver for property type
# assertions for self.e.driver
from seneca.db.driver import AbstractDatabaseDriver, ContractDriver
from seneca.execution.module import DatabaseFinder


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.e = Executor()

    def tearDown(self):
        del self.e

    def test_init(self):
        self.assertEqual(self.e.concurrency, True, 'Concurrency not set to True by default.')
        self.assertEqual(self.e.metering, True, 'Metering not set to true by default.')

    def test_dynamic_init(self):
        e = Executor(metering=False, concurrency=False)

        self.assertEqual(e.metering, False, 'Metering is not set to false after dynamic set')
        self.assertEqual(e.concurrency, False, 'Concurrency is not set to false after dynamic set.')

    def test_driver_resolution(self):
        # The CRDriver class is not able to be isolated so this test is turned off for now
        # Colin TODO: Discuss with Davis how we update CRDriver (or isolate the concept)
        #self.assertIsInstance(self.e.driver, conflict_resolution.CRDriver, 'Driver type does not resolve to CRDriver type when concurrency is True')

        e = Executor(concurrency=False)
        self.assertIsInstance(e.driver, AbstractDatabaseDriver, 'Driver does not resolve to AbstractDatabaseDriver when concurrency is False')


driver = ContractDriver(db=0)


class TestSandboxWithDB(unittest.TestCase):
    def setUp(self):
        sys.meta_path.append(DatabaseFinder)
        driver.flush()
        contracts = glob.glob('./test_sys_contracts/*.py')
        self.author = 'unittest'
        self.sb = Sandbox()
        self.mpsb = MultiProcessingSandbox()

        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            driver.set_contract(name=name, code=code, author=self.author)

    def tearDown(self):
        self.mpsb.terminate()
        sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def test_base_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}

        status_code, result = self.sb.execute(self.author, contract_name,
                                              function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_multiproc_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}

        status_code, result = self.mpsb.execute(self.author, contract_name,
                                                function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_base_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.sb.execute(self.author, contract_name,
                                              function_name, kwargs)
        self.assertEqual(status_code, 1)

    def test_multiproc_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.mpsb.execute(self.author, contract_name,
                                                function_name, kwargs)
        self.assertEqual(status_code, 1)


if __name__ == "__main__":
    unittest.main()
