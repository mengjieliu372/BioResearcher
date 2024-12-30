const fs = require('fs');
fs.readFile('./nihms-2028845_report.json', 'utf-8', (err, data) => {
    if (err) {
        console.error(err);
        return;
    }
    
    const processData = data
        .replace(/\\n/g, '')
        .replace(/\\"/g, '"')
        .replace(/\\\\n/g, '')
        .replace(/"{/g, '{')
        .replace(/}"/g, '}');

    const jsonData = JSON.parse(processData);
    fs.writeFile('./output.json', jsonData, (err) => {
        if (err) {
            console.error(err);
            return;
        }
    });
});