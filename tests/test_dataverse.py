import unittest
import shutil, tempfile
import json
from os import path
from importlib.resources import files
from irods2dataverse.to_dataverse import (
    get_dataset,
    validate_md,
)
from irods2dataverse import customClass


# test validating against the Demo class
class TestMdValidation(unittest.TestCase):
    """Test the following in validate_md()

    1. That when `md` is a string it will try to read the file
      1a. It will work when the path is valid
      1b. It will fail when the path is not valid (`read_file()` will?)
    2. That when `md` is a dictionary, it will still read the metadata
      2a. It will work when the metadata is valid
      2b. It will fail when it is not valid
    3. If the installation is RDR, RDR metadata should pass and Demo metadata should fail
    4. If the installation is Demo, Demo metadata should pass and RDR metadata should fail
    No need to test long and short, or ManGO md, since this is covered by avu2json
    """

    def setUp(self):
        self.name = "Demo"
        self.alias = "demo"
        self.expected_class = customClass.DemoDataset
        self.test_dir = tempfile.mkdtemp(self.name)
        self.ds = get_dataset(self.name)

    def test_dataset(self):
        self.assertIsInstance(self.ds, self.expected_class)
        self.assertEqual(self.ds.alias, self.alias)
        self.assertTrue(self.ds.metadata_template.exists())
        self.assertTrue(self.ds.mango_schema.exists())

    def test_correct_validation(self):
        """Test that the contents of the metadata template are validated as correct"""
        with self.ds.metadata_template.open("r") as f:
            self.metadict = json.load(f)
        self.assertTrue(validate_md(self.ds, self.metadict))
        self.assertTrue(validate_md(self.ds, str(self.ds.metadata_template)))

    def test_failing_validation(self):
        """Test different kinds of invalid inputs"""
        self.assertFalse(validate_md(self.ds, 5))
        self.assertFalse(validate_md(self.ds, {"a": 1, "b": 2}))
        with self.assertRaises(FileNotFoundError):
            validate_md(self.ds, "This is an invalid string")

    def tearDown(self):
        shutil.rmtree(self.test_dir)


class TestMdValidationRDR(TestMdValidation):
    def setUp(self):
        self.name = "RDR"
        self.alias = "rdr"
        self.expected_class = customClass.RDRDataset
        self.test_dir = tempfile.mkdtemp(self.name)
        self.ds = get_dataset(self.name)


class TestMdValidationRDRPilot(TestMdValidation):
    def setUp(self):
        self.name = "RDR-pilot"
        self.alias = "rdr"
        self.expected_class = customClass.RDRPilotDataset
        self.test_dir = tempfile.mkdtemp(self.name)
        self.ds = get_dataset(self.name)
