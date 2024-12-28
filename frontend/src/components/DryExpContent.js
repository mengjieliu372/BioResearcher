import React from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { useState } from 'react';

function InnerComponent({ tasks }) {
    const [expandedAll, setExpandedAll] = useState(false);
    const [expandedArray, setExpandedArray] = useState(Array(tasks.length).fill(false));
    const handleExpandedAll = () => {
        setExpandedAll(prev => {
            const newExpandedAll = !prev;
            setExpandedArray(Array(tasks.length).fill(newExpandedAll));
            return newExpandedAll;
        });
    };
    const handleExpandArray = (index) => {
        const newArray = [...expandedArray];
        newArray[index] = !newArray[index];
        setExpandedArray(newArray);
    };

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6,mb: 1,textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Parts' : 'Expand All Steps'}
                </Button>
            </Box>

            {tasks.map((task, index) => (
                <Accordion key={index} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => handleExpandArray(index)}
                    >
                        {task.task_id}
                    </AccordionSummary>
                    <AccordionDetails>
                        <Typography variant="h6" sx={{fontWeight: 'bold'}}>Description:</Typography>
                        <Typography variant="body1">{task.task_description}</Typography>

                        <Typography variant="h6" sx={{fontWeight: 'bold'}}>Input:</Typography>
                        <Typography variant="body1">{task.input}</Typography>
                        
                        <Typography variant="h6" sx={{fontWeight: 'bold'}}>Output:</Typography>
                        <Typography variant="body1">Output:{task.output}</Typography>
                    </AccordionDetails>
                </Accordion>
            ))}
        </Box>
    );
}


function RenderContent({ data }) {
    const [expandedAll, setExpandedAll] = useState(false);
    const [expandedArray, setExpandedArray] = useState(Array(Object.keys(data).length).fill(false));
    const handleExpandedAll = () => {
        setExpandedAll(prev => {
            const newExpandedAll = !prev;
            setExpandedArray(Array(Object.keys(data).length).fill(newExpandedAll));
            return newExpandedAll;
        });
    };
    const handleExpandArray = (index) => {
        const newArray = [...expandedArray];
        newArray[index] = !newArray[index];
        setExpandedArray(newArray);
    };

    return (
        <Container>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6,mb: 1,textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Parts' : 'Expand All Parts'}
                </Button>
            </Box>

            {Object.entries(data).map(([part, tasks], index) => (
                <Accordion key={part} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => handleExpandArray(index)}
                    >
                        {part}
                    </AccordionSummary>
                    <AccordionDetails>
                        <InnerComponent tasks={tasks} />
                    </AccordionDetails>
                </Accordion>
            ))}
        </Container>
    );
}

export default RenderContent;