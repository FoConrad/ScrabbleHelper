// content of index.js
const child_process = require('child_process')
const http = require('http')

const port = 3000


const requestHandler = (request, response) => {
    console.log(request.url)
    var pythonProcess = child_process.spawn('python3',
        ["scrabble_helper/score_hand.py", "print_board"]);
    pythonProcess.stdout.on('data', function (data){
        // Do something with the data returned from python script
        response.write(data)
    });
    pythonProcess.on('exit', function() {
        response.write('\n\n')
        //response.write('Message from TJ here')
        response.end('An example scrabble board, above')
    })
}

const server = http.createServer(requestHandler)

server.listen(port, (err) => {
    if (err) {
        return console.log('something bad happened', err)
    }
    console.log(`server is listening on ${port}`)
})
