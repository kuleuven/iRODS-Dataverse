# curl --help all

# # Request direct upload (Demo Installation)
# export API_TOKEN=605344cc-933e-4be2-9fe7-a64802bf4132
# export SERVER_URL=https://demo.dataverse.org
# # export PERSISTENT_IDENTIFIER=doi:10.70122/FK2/K7KGHG # draft
# export PERSISTENT_IDENTIFIER=doi:10.70122/FK2/DJ6YQF # published
# export SIZE=1000000000
# curl -H "X-Dataverse-key:$API_TOKEN" "$SERVER_URL/api/datasets/:persistentId/uploadurls?persistentId=$PERSISTENT_IDENTIFIER&size=$SIZE"
# # Response:
# # draft:
# # {"status":"ERROR","message":"Direct upload not supported for files in this dataset: 2354300"}
# # published:
# # {"status":"ERROR","message":"Direct upload not supported for files in this dataset: 2353343"}

# Request direct upload (RDR Demo Installation at https://www.rdm.libis.kuleuven.be/)
export API_TOKEN=6b7a80f2-e065-4285-8f9e-90bbc6826855
export SERVER_URL=https://rdr.kuleuven.be/
export PERSISTENT_IDENTIFIER=doi:10.48804/RQLUMN # draft https://doi.org/10.82111/CQ5E9L
export SIZE=100000
curl -H "X-Dataverse-key:$API_TOKEN" "$SERVER_URL/api/datasets/:persistentId/uploadurls?persistentId=$PERSISTENT_IDENTIFIER&size=$SIZE"

# curl -H "X-Dataverse-key:9f8db8e5-1fba-425d-8077-472e913e9cf5" "https://www.rdm.libis.kuleuven.be/api/datasets/:persistentId/uploadurls?persistentId=doi:10.82111/CQ5E9L&size=1024"


# Response:
# {"status":"ERROR","message":"Dataset with Persistent ID doi:10.82111/CQ5E9L, not found."}
# Using a published URL was not tested; I submitted for review in RDR.


# export API_TOKEN=6b7a80f2-e065-4285-8f9e-90bbc6826855
# export SERVER_URL=https://rdr.kuleuven.be/
# export PERSISTENT_IDENTIFIER=doi:10.48804/RQLUMN
# export SIZE=10000000



# Is it possible to direct upload in the published version? 



