import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useState } from 'react';

// 内部组件
function InnerComponent({ steps }) {
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
            {Object.entries(steps).slice(1).map(([step, details], index) => {
                const lines = details["implementation details"]
                    .split('\n')
                    .map(line => line.trim());

                const title = lines.shift();
                const description = lines.join('\n');

                return (
                    <Box>
                        <Accordion key={step} expanded={expandedArray[index]}>
                            <AccordionSummary
                                expandIcon={<ExpandMoreIcon />}
                                aria-controls="panel1a-content"
                                id="panel1a-header"
                                onClick={() => { handleExpandArray(index) }}
                            >
                                <strong>{title}</strong>
                            </AccordionSummary>
                            <AccordionDetails>
                                {description.split('\n').map((line, index) => (
                                    <Box key={index} sx={{ textIndent: '2ch' }}>
                                        {line}
                                    </Box>
                                ))}
                                <Box mt={2}>
                                    <strong>Reference Source:</strong>
                                    {Object.entries(details["Reference Source"]).map(
                                        ([source, parts]) => (
                                            <Box key={source}>
                                                {Object.entries(parts).map(([part, steps]) => (
                                                    <Box key={part}>
                                                        {Object.entries(steps).map(([step, details]) => (
                                                            <Box key={step}>
                                                                {`${source}: ${part} ${step}`}
                                                            </Box>
                                                        ))}
                                                    </Box>
                                                ))}
                                            </Box>
                                        )
                                    )}
                                </Box>
                            </AccordionDetails>
                        </Accordion>
                    </Box>
                );
            })}
        </Box>
    );
}


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
        <Container>
            <Button onClick={handleExpandedAll} variant='outlined'>
                {expandedAll ? 'Collapse All' : 'Expand All'}
            </Button>
            {Object.entries(data).map(([part, steps], index) => (
                <Accordion key={part} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => handleExpandArray(index)}
                    >
                        <strong>{part + ": " + steps[part]}</strong>
                    </AccordionSummary>
                    <AccordionDetails>
                        <InnerComponent steps={steps} />
                    </AccordionDetails>
                </Accordion>
            ))}
        </Container>
    );
}
