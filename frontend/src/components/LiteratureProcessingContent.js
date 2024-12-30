import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import { useState } from 'react';
import { getPaperInfo } from '../services/api';

function InnerComponent({ part, steps, analysis }) {
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
            {analysis[part] && (
                <>
                    <Box>
                        <Typography variant="h5">Reference Reason:</Typography>
                        {analysis[part]["Reason"]}
                    </Box>
                    <Box>
                        <Typography variant="h5">Suggestions:</Typography>
                        {analysis[part]["Suggestions"]}
                    </Box>
                </>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6, mb: 1, textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Steps' : 'Expand All Steps'}
                </Button>
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

export default function RenderContent({ report, analysis, paper_title}) {
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
        <Box>
            <Typography variant='h6'>
                {paper_title}
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6, mb: 1, textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Parts' : 'Expand All Parts'}
                </Button>
            </Box>
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
                            {analysis[part] && analysis[part]["Referability"] && (
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
                            )}
                        </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                        <InnerComponent part={part} steps={steps} analysis={analysis} />
                    </AccordionDetails>
                </Accordion>
            ))}
        </Box>
    );
}
