const express = require('express')
const cors = require('cors');
const { spawn } = require('child_process')  // require spawn to run external executables
const app = express()
const port = 8383

app.use(express.static('website'))
app.use(express.json())
app.use(cors())

app.get('/info', (req, res) => {
    res.status(200).json({ info: 'preset text ' })
})

app.post('/', (req, res) => {
    // Extract both parcels from the request body
    const { parcel, parcel2 } = req.body
    console.log('parcel:', parcel)
    console.log('parcel2:', parcel2)
    
    if (!parcel || !parcel2) {
        return res.status(400).send({ status: 'failed' })
    }

    // Spawn the brain executable passing both values as arguments.
    const brainProcess = spawn('./brain', [parcel, parcel2], {
        env: {
            ...process.env,
            DYLD_LIBRARY_PATH: '/usr/local/lib' 
        }
    });

    let output = ''

    // Collect standard output.
    brainProcess.stdout.on('data', (data) => {
        output += data.toString()
    })

    // Log any errors from brain.
    brainProcess.stderr.on('data', (data) => {
        console.error(`Error from brain: ${data}`)
    })

    brainProcess.on('close', (code) => {
        console.log(`brain process exited with code ${code}`)
        // Send the brain.cpp result back to the client.
        res.status(200).send({ status: 'received', result: output })
    })
})

app.listen(port, () => console.log(`Server has started on port: ${port}`))