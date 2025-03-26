import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Tooltip,  { tooltipClasses } from '@mui/material/Tooltip';
import { useState } from 'react';
import Divider from '@mui/material/Divider';
import { styled } from '@mui/material/styles';

function InnerComponent({ stepData }) {

    const CustomWidthTooltip = styled(({ className, ...props }) => (
        <Tooltip {...props} classes={{ popper: className }} />
      ))({
        [`& .${tooltipClasses.tooltip}`]: {
          maxWidth: 500,
        },
      });
    
    const analysisColor = {
        "High": "#6BCF73",
        "Medium": "#FFA726",
        "Low": "#EF9A9A"
    }

    return (
        <Box>
            {Object.entries(stepData)
                .filter(([stepKey, stepValue]) => stepKey !== "Referability" && stepKey !== "Reason" && stepKey !== "Suggestions")
                .slice(1)
                .map(([stepKey, stepValue], index) => (
                    <Box key={stepKey}>
                        <Typography variant='h6'>{stepKey.charAt(0).toUpperCase() + stepKey.slice(1)}</Typography>
                        <Box>
                            {
                                !(typeof stepValue === 'object') ? (
                                    <Box>
                                        <Typography variant='body1'>{stepValue}</Typography>
                                    </Box>

                                ) : (
                                    <Box>
                                        <Box>
                                            <Typography variant='body1'>
                                                {stepValue["implementation details"] || "No data available"}
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', pr: 5 }}>
                                            <CustomWidthTooltip
                                                arrow
                                                placement='left'
                                                title={
                                                    <Box>
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
                                                }
                                            >
                                                <Button variant="outlined">Reference</Button>
                                            </CustomWidthTooltip>
                                        </Box>
                                    </Box>

                                )
                            }
                        </Box>
                    </Box>
                ))}
            <Box sx={{ width: '100%', backgroundColor: analysisColor[stepData["Referability"]] || '#cbf1f5', p: 1, mt:1, borderRadius: '8px' }}>
                <Typography variant='h6' sx={{ ml: 1 }}>Analysis:</Typography>
                <Box sx={{ display: 'flex', width: '100%' }}>
                    <Box sx={{ width: '50%', m: 1, p: 1, border: '1px solid #000', borderRadius: '8px' }}>
                        <Typography variant='subtitle1'>Reason:</Typography>
                        <Typography variant='body1'>{stepData["Reason"]}</Typography>
                    </Box>
                    <Box sx={{ width: '50%', m: 1, p: 1, border: '1px solid #000', borderRadius: '8px' }}>
                        <Typography variant='subtitle1'>Suggestions:</Typography>
                        <Typography variant='body1'>{stepData["Suggestions"]}</Typography>
                    </Box>
                </Box>
            </Box>
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
                            <InnerComponent stepData={partValue} />
                        </AccordionDetails>
                    </Accordion>
                ))}
            </Box>
        </Box>
    );
}
