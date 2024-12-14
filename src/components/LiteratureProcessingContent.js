import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import { useState } from 'react';

function InnerComponent({part, steps, analysis}) {
    const [expandedAll, setExpandedAll] = useState(false);
    const [expandedArray, setExpandedArray] = useState(Array(Object.keys(steps).length).fill(false));
    const handleExpandedAll = () => {
        setExpandedAll(prev => {
            const newExpandedAll = !prev;
            setExpandedArray(Array(Object.keys(steps).length).fill(newExpandedAll));
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
            <Button onClick={handleExpandedAll} variant='outlined'>
                {expandedAll ? 'Collapse All' : 'Expand All'}
            </Button>
            <Box>
                <Typography variant='h5' >Reference Reason:</Typography>
                {analysis[part]["Reason"]}
            </Box>
            <Box>
                <Typography variant='h5' >Suggestions:</Typography>
                {analysis[part]["Suggestions"]}
            </Box>
            {Object.entries(steps)
                .slice(1)
                .map(([step, details], index) => (
                    <Accordion key={step} expanded={expandedArray[index]}>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                            onClick={() => handleExpandArray(index)}
                        >
                            {step}
                        </AccordionSummary>
                        <AccordionDetails>
                            <Box>
                                <Typography variant='h6'>Implementation Details:</Typography>
                                {details["implementation details"]}
                            </Box>
                            <div>
                                <Typography variant='h6'>Original text:</Typography>
                                {details["original text"]}
                            </div>
                            <div>
                                <Typography variant='h6'>Results:</Typography>
                                {details["results"]}
                            </div>
                            <div>
                                <Typography variant='h6'>Results original text:</Typography>
                                {details["results original text"]}
                            </div>
                        </AccordionDetails>
                    </Accordion>
                ))}
        </Box>
    );
}

export default function RenderContent({ report, analysis }) {
    const [expandedAll, setExpandedAll] = useState(false);
    const [expandedArray, setExpandedArray] = useState(Array(Object.keys(report).length).fill(false));
    const handleExpandedAll = () => {
        setExpandedAll(prev => {
            const newExpandedAll = !prev;
            setExpandedArray(Array(Object.keys(report).length).fill(newExpandedAll));
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
            <Button onClick={handleExpandedAll} variant='outlined'>
                {expandedAll ? 'Collapse All' : 'Expand All'}
            </Button>
            {Object.entries(report).map(([part, steps], index) => (
                <Accordion key={part} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => handleExpandArray(index)}
                    >
                        {part + ": " + steps[part]}
                        <Box sx={{ ml: 'auto' }}>
                            <Chip
                                label={`Referability: ${analysis[part]["Referability"]}`}
                                color={
                                    analysis[part]["Referability"] === 'High'
                                        ? 'success'
                                        : analysis[part]["Referability"] === 'Medium'
                                            ? 'warning'
                                            : 'error'
                                }
                                size="small"
                            />
                        </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                        <InnerComponent part={part} steps={steps} analysis={analysis} />
                    </AccordionDetails>
                </Accordion>
            ))}
        </Container>
    );
}
