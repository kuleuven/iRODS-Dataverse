
ApiConfig.init('https://demo.dataverse.org', DataverseApiAuthMechanism.API_KEY, '605344cc-933e-4be2-9fe7-a64802bf4132')
/* 
...
DV_URL = "https://demo.dataverse.org"
API_TOKEN = "605344cc-933e-4be2-9fe7-a64802bf4132"
...
*/

import { uploadFile } from '@iqss/dataverse-client-javascript'

function App() {

    // Upload a file to a remote S3 Storage

    const datasetId = 'doi:10.70122/FK2/K7KGHG'
    const file = new File(['content'], 'example.txt', { type: 'text/plain' })
    const progressCallback = (progress) => console.log(`Upload progress: ${progress}%`)
    const abortController = new AbortController()

    uploadFile.execute(datasetId, file, progressCallback, abortController).then((storageId) => {
        console.log(`File uploaded successfully with storage ID: ${storageId}`)
    })

    /* ... */

}

export default App


/* ----- Basic structure for a React application ----- */

// my-app/
// ├── README.md
// ├── node_modules/
// ├── package.json
// ├── .gitignore
// ├── public/
// │   ├── favicon.ico
// │   ├── index.html
// │   └── manifest.json
// └── src/
//     ├── App.css
//     ├── App.js
//     ├── App.test.js
//     ├── index.css
//     ├── index.js
//     ├── logo.svg
//     └── serviceWorker.js


// To RUN the js code: 
// Open JavaScript Code in VSCode after installing the code runner extension. 
// To run the code, use the CTRL+ALT+N shortcut or hit F1 and enter Run Code. 
// You will then see the output in the “OUTPUT” tab.

