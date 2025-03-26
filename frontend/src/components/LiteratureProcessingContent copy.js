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
import Divider from '@mui/material/Divider';
import { PieChart } from '@mui/x-charts/PieChart';

function InnerComponent({ setpData }) {
    const [expandedAll, setExpandedAll] = useState(false);
    const [expandedArray, setExpandedArray] = useState(Array(Object.keys(setpData).length).fill(false));
    const handleExpandedAll = () => {
        setExpandedAll(prev => {
            const newExpandedAll = !prev;
            setExpandedArray(Array(Object.keys(setpData).length).fill(newExpandedAll));
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
            {Object.entries(setpData)
                .filter(([stepKey, stepValue]) => stepKey !== "Referability")
                .slice(1)
                .map(([stepKey, stepValue], index) => (
                    <Accordion key={stepKey} expanded={expandedArray[index]}>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                            onClick={() => handleExpandArray(index)}
                        >
                            {stepKey}
                        </AccordionSummary>
                        <AccordionDetails>
                            {
                                !(typeof stepValue === 'object') ? (
                                    <Box>
                                        <Typography variant='body1'>{stepValue}</Typography>
                                    </Box>
                                ) : (
                                    <Box>
                                        <Box>
                                            <Typography variant='h6'>Implementation Details:</Typography>
                                            <Typography variant='body1'>
                                                {stepValue["implementation details"] || "No data available"}
                                            </Typography>
                                        </Box>
                                        <Box>
                                            <Typography variant='h6'>Original Text:</Typography>
                                            <Typography variant='body1'>
                                                {stepValue["original text"] || "No data available"}
                                            </Typography>
                                        </Box>
                                        <Box>
                                            <Typography variant='h6'>Results:</Typography>
                                            <Typography variant='body1'>
                                                {stepValue["results"] || "No data available"}
                                            </Typography>
                                        </Box>
                                        <Box>
                                            <Typography variant='h6'>Results Original Text:</Typography>
                                            <Typography variant='body1'>
                                                {stepValue["results original text"] || "No data available"}
                                            </Typography>
                                        </Box>
                                    </Box>

                                )
                            }
                        </AccordionDetails>
                    </Accordion>
                ))}
        </Box>
    );
}

export default function RenderContent({ data, paper_title }) {
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

    // 遍历data，计算Referability为High, Medium, Low的数量
    let referabilityCount = { High: 0, Medium: 0, Low: 0 };
    let sum = 0;
    Object.values(data).forEach((part) => {
        if (!part["Referability"]) return;
        if (part["Referability"] === "High") {
            referabilityCount["High"] += 1;
        } else if (part["Referability"] === "Medium") {
            referabilityCount["Medium"] += 1;
        } else if (part["Referability"] === "Low") {
            referabilityCount["Low"] += 1;
        }
        sum += 1;
    });
    // 计算百分比并生成饼图数据
    let referabilityData = [];
    Object.entries(referabilityCount).forEach(([key, value], index) => {
        referabilityData.push({ id: index, value: value / sum, label: key, color: key === "High" ? "#2b762f" : key === "Medium" ? "#ed6c02" : "#d32f2f" });
    });

    return (
        <Box>
            {/* 顶部的标题 */}
            <Box>
                <Typography variant='h6'>
                    {paper_title}
                </Typography>
            </Box>
            <Divider />
            {/* 具体内容展示 */}
            <Box sx={{
                height: '58vh',
                width: '56vw',
                ml: 'auto',
                mr: 'auto',
                mt: '1vh',
                overflowY: 'auto',
                maxHeight: '58vh',
                borderRadius: '8px',
                boxShadow: 3,
            }}>
                {Object.entries(data).map(([partKey, partValue], index) => (
                    <Accordion key={partKey} expanded={expandedArray[index]}>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                            onClick={() => handleExpandArray(index)}
                        >
                            <Typography variant='subtitle'>
                                {partKey + ": " + partValue[partKey]}
                            </Typography>
                            <Box sx={{ ml: 'auto' }}>
                                {partValue["Referability"] && (
                                    <Chip
                                        label={`Referability: ${partValue["Referability"]}`}
                                        color={
                                            partValue["Referability"] === 'High'
                                                ? 'success'
                                                : partValue["Referability"] === 'Medium'
                                                    ? 'warning'
                                                    : 'error'
                                        }
                                        size="small"
                                    />
                                )}
                            </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                            <InnerComponent setpData={partValue} />
                        </AccordionDetails>
                    </Accordion>
                ))}
            </Box>
        </Box>
    );
}
