import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useState } from 'react';
import Typography from '@mui/material/Typography';



export default function RenderContent({ data }) {
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
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6, mb: 1, textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Parts' : 'Expand All Parts'}
                </Button>
            </Box>
            {Object.entries(data).map(([filename, code_txt], index) => (
                <Accordion key={filename} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => handleExpandArray(index)}
                    >
                        <strong>{filename}</strong>
                    </AccordionSummary>
                    <AccordionDetails>
                        <pre>{code_txt}</pre>
                    </AccordionDetails>
                </Accordion>
            ))}
        </Box>
    );
}
