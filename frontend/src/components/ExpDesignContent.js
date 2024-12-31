import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useState } from 'react';
import Typography from '@mui/material/Typography';


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
            {/*展开所有steps*/}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={handleExpandedAll} variant='contained'
                    sx={{ mr: 6, mb: 1, textTransform: 'none' }}
                >
                    {expandedAll ? 'Collapse All Steps' : 'Expand All Steps'}
                </Button>
            </Box>

            {Object.entries(steps).slice(1).map(([step, details], index) => (
                <Accordion key={index} expanded={expandedArray[index]}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        onClick={() => { handleExpandArray(index) }}
                    >
                        {step}
                    </AccordionSummary>
                    <AccordionDetails>
                        <Box>
                            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Implementation Details:</Typography>
                            <Typography variant='body'>{details["implementation details"]}</Typography>
                        </Box>
                        <Box>
                            {details["Reference Source"] && (
                                <>
                                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Reference Source:</Typography>
                                    {typeof details["Reference Source"] === "string" ? (
                                        // "Reference Source" 是一个字符串，直接显示它
                                        <Box>{details["Reference Source"]}</Box>
                                    ) : (
                                        // 是对象，则执行嵌套的 map 渲染
                                        Object.entries(details["Reference Source"]).map(([group, items]) => (
                                            items && Object.keys(items).length > 0 && (
                                                <Box key={group}>
                                                    <Typography>{group}</Typography>
                                                    {Object.entries(items).map(([itemKey, subItems]) => (
                                                        subItems && subItems.length > 0 && (
                                                            <Box key={itemKey}>
                                                                <Typography>{itemKey}</Typography>
                                                                {subItems.map((value, index) => (
                                                                    <Box key={index}>{value}</Box>
                                                                ))}
                                                            </Box>
                                                        )
                                                    ))}
                                                </Box>
                                            )
                                        ))
                                    )}
                                </>
                            )}
                        </Box>

                    </AccordionDetails>
                </Accordion>
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
                        <strong>{part + ": " + steps[part]}</strong>
                    </AccordionSummary>
                    <AccordionDetails>
                        <InnerComponent steps={steps} />
                    </AccordionDetails>
                </Accordion>
            ))}
        </Box>
    );
}
