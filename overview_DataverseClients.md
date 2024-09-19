**This overview was last updated and shared in MS Teams chat on 22 February 2024**

These clients where investigated before choosing a client for the iRODS-Dataverse integration. The choice of client was made according to the following parameters: 
- which client provides more functionalities.
- which client has been more actively maintained.
- which client has better documentation.
- which client is written in a language the developer is comfortable with.


| Module                       |  Last commit  |   Fit        |  Link                                                                         | Python version |
|:-----------------------------|:-------------:|:------------:|:-----------------------------------------------------------------------------:|:--------------:|
| **pyDataverse**              |  Dec 13, 2023 |  create draft, sumbit, remove, private URL, DOI, metadata   | <a href='https://github.com/gdcc/pyDataverse'>Link</a>                              | 3.6, 3.7, 3.8 |
| **python-dvuploader**        |  Jan 16, 2024 |  bulk, parallel upload, checksum      |  <a href='https://github.com/gdcc/python-dvuploader'>Link</a>                             | ........... |
| **EasyDataverse**            |  Dec 27, 2023 |  got stuck   | <a href='https://github.com/gdcc/easyDataverse'>Link</a>                                         | ........... |
| **dataverse-client-python**  |  Jul 01, 2019 |     inactive module        | <a href='https://github.com/CenterForOpenScience/osf.io/tree/develop/addons/dataverse'>Link</a>  | ........... |
| **Pooch**                    |  Feb 20, 2024 |  download, checksum, decompress files, unpack archives   |  <a href='https://github.com/fatiando/pooch'>Link</a>              | ........... |
| **idsc.dataverse**           |  Nov 08, 2023 |  primary, migrate from one Dataverse to another    | <a href='https://github.com/iza-institute-of-labor-economics/idsc.dataverse'>Link</a>          | ........... |


**Notes**

- Check preliminary work on the overview of clients per section of the *complete iRODS-Dataverse integration workflow: Authenticate - Metadata - Create Draft - Publish - Update*, at local file README_api-calls.md.

- If the iRODS-Dataverse integration remains a user script, using the R client https://github.com/IQSS/dataverse-client-r could provide an interesting extension.

- For *multiple file upload* with ZIP check the SWORD upload ZIP file with Java library https://github.com/IQSS/dataverse-client-java.
