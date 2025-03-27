import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useState } from 'react';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';



function InnerComponent({ steps }) {
    return (
        <Box>
            <Box sx={{ width: '100%', backgroundColor: '#e3fdfd', p: 1, mt: 1, borderRadius: '8px' }}>
                <Typography variant='h6' sx={{ ml: 1 }}>About this Part:</Typography>
                <Box sx={{ display: 'flex', width: '100%' }}>
                    <Box sx={{ width: '50%', m: 1, p: 1, border: '1px solid #000', borderRadius: '8px' }}>
                        <Typography variant='subtitle1'>Purpose:</Typography>
                        <Typography variant='body1'>{steps["Purpose"]}</Typography>
                    </Box>
                    <Box sx={{ width: '50%', m: 1, p: 1, border: '1px solid #000', borderRadius: '8px' }}>
                        <Typography variant='subtitle1'>Design Reason:</Typography>
                        <Typography variant='body1'>{steps["Design Reason"]}</Typography>
                    </Box>
                </Box>
            </Box>
            {Object.entries(steps)
                .filter(([step]) => step !== "Purpose" && step !== "Design Reason")
                .slice(1)
                .map(([step, details], index) => (
                    <Box x={index}>
                        <Typography variant='h6'>{step.charAt(0).toUpperCase() + step.slice(1)}</Typography>
                        <Box>
                            <Box>
                                <Typography variant='body'>{details["implementation details"]}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'flex-end', pr: 5 }}>
                                <Tooltip
                                    arrow
                                    placement='left'
                                    title={details["Reference Source"] && (
                                        <>
                                            {typeof details["Reference Source"] === "string" ? (
                                                // "Reference Source" 是一个字符串，直接显示它
                                                <Typography>{details["Reference Source"]}</Typography>
                                            ) : (
                                                <pre>
                                                    {JSON.stringify(details["Reference Source"], null, 2)}
                                                </pre>
                                            )}
                                        </>
                                    )}
                                >
                                    <Button variant="outlined">Reference</Button>
                                </Tooltip>
                            </Box>
                        </Box>
                    </Box>
                ))}
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
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6, mb: 1, textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Parts' : 'Expand All Parts'}
                </Button>
            </Box>
            {Object.entries(data).map(([part, steps], index) => (
                <Accordion key={part} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => handleExpandArray(index)}
                    >
                        <Typography variant='h6'>{part + ": " + steps[part]}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <InnerComponent steps={steps} />
                    </AccordionDetails>
                </Accordion>
            ))}
        </Box>
    );
}
