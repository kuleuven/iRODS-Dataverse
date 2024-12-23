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
from unittest.mock import patch, Mock
from irods2dataverse.to_dataverse import deposit_ds


# test validating against the Demo class
class TestMdValidation(unittest.TestCase):
    """Test dataset properties and validation
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


# For new classes, create a new child of TestMdValidation with the appropriate attributes


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


class TestAPI(unittest.TestCase):

    @patch("irods2dataverse.to_dataverse.NativeApi")
    def test_deposit(self, api):
        api.create_dataset.return_value.json.return_value = {
            "status": 200,
            "data": {"persistentId": "someid", "id": "anotherid"},
        }
        ds = get_dataset("Demo")
        dsStatus, dsPID, dsID = deposit_ds(api, ds)
        self.assertEqual(dsStatus, 200)
        self.assertEqual(dsPID, "someid")
        self.assertEqual(dsID, "anotherid")

    # md = to_dataverse.deposit_df(api, dsPID, item.name, trg_path)

    # fileURL, storageID = direct_upload.get_du_url(
    #             ds.baseURL, dsPID, objSize, header_key
    #         )
