import * as React from 'react';
import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepButton from '@mui/material/StepButton';
import { useNavigate, useParams } from 'react-router-dom';
import { Outlet } from 'react-router-dom';
import { getCompletedSteps, getProject } from '../services/api';
import { Typography } from '@mui/material';

const steps = [
    'Search',
    'Literature Processing',
    'Experimental Design',
    'Dry Experiments',
    'Programming',
];

export default function HorizontalLinearAlternativeLabelStepper() {
    const [activeStep, setActiveStep] = React.useState(0);
    const navigate = useNavigate();
    const { id } = useParams();
    const [completedSteps, setCompletedSteps] = useState([]);
    const [exp, setExp] = useState();
    const handleStep = (step) => () => {
        setActiveStep(step);
        switch (step) {
            case 0:
                navigate(`/${id}/steps/search`);
                break;
            case 1:
                navigate(`/${id}/steps/literature-processing`);
                break;
            case 2:
                navigate(`/${id}/steps/experimental-design`);
                break;
            case 3:
                navigate(`/${id}/steps/dry-experiments`);
                break;
            case 4:
                navigate(`/${id}/steps/programming`);
                break;
            default:
                break;
        }
    };

    // 获取已完成步骤
    const fetchStepsCompleted = async () => {
        try {
            const response = await getCompletedSteps(id);
            setCompletedSteps(response.data);
        }
        catch (error) {
            console.log(error);
        }
    }

    // 获取当前实验信息
    const fetchProject = async () => {
        try {
            const response = await getProject(id);
            setExp(response.data);
        }
        catch (error) {
            console.log(error);
        }
    }

    useEffect(() => {
        fetchStepsCompleted();
        fetchProject();
    }, []);

    // 轮询
    useEffect(() => {
        const interval = setInterval(() => {
            fetchStepsCompleted();
        }, 1000);

        if (completedSteps.length === steps.length) {
            clearInterval(interval);
        }

        return () => clearInterval(interval);
    }, [id, activeStep, completedSteps]);

    if (!exp) {
        return <Typography>Loading...</Typography>;
    }

    return (
        <Box>
            <Box
                sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '10vh',
                }}
            >
                <Stepper
                    nonLinear
                    activeStep={activeStep}
                    alternativeLabel
                    sx={
                        {
                            height: '6vh',
                            backgroundColor: '#fff', // 外部背景色
                            borderRadius: '8px',
                            padding: '16px',
                            boxShadow: 2,
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            width: '70%',
                        }
                    }
                >
                    {steps.map((label, index) => (
                        <Step key={label} completed={completedSteps.includes(index)}>
                            <StepButton
                                color="inherit"
                                onClick={handleStep(index)}
                                disabled={!completedSteps.includes(index)} // 未完成的步骤不可点击
                                sx={{
                                    height: '4vh',
                                }}
                            >
                                {label}
                            </StepButton>
                        </Step>
                    ))}
                </Stepper>
            </Box>

            <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',  // 上对齐
                mt: 2,
                mx: '5vw',  // 左右间距
            }}>
                <Box
                    sx={{
                        width: '17vw',
                        backgroundColor: '#ffffff',
                        height: '75vh',
                        maxHeight: '75vh',
                        overflowY: 'auto',
                        paddingLeft: '16px',
                        paddingRight: '16px',
                        borderRadius: '8px',
                    }}
                >
                    <Typography variant="h5" align="center" sx={{mt: '2vh', mb: '2vh', color: '#2274f2', fontWeight: 'bold'}}>Task Information</Typography>

                    <Typography variant="h6" sx={{color: '#3b82f6'}}>Experiment Name:</Typography>
                    <Typography variant="body1">{exp.expName}</Typography>

                    <Typography variant="h6" sx={{color: '#3b82f6', mt: 1}}>Experiment Purpose:</Typography>
                    <Typography variant="body1">{exp.expPurpose}</Typography>

                    <Typography variant="h6" sx={{color: '#3b82f6', mt: 1}}>Paper Source:</Typography>
                    <Typography variant="body1">PMC: {exp.paperset.PMC ? 'Yes' : 'No'}</Typography>
                    <Typography variant="body1">PubMed: {exp.paperset.PubMed ? 'Yes' : 'No'}</Typography>

                    <Typography variant="h6" sx={{color: '#3b82f6', mt: 1}}>Dataset Source:</Typography>
                    <Typography variant="body1">GEO: {exp.dataset.GEO ? 'Yes' : 'No'}</Typography>
                    <Typography variant="body1">NCBI: {exp.dataset.NCBI ? 'Yes' : 'No'}</Typography>
                    <Typography variant="body1">cBioPortal: {exp.dataset.cBioPortal ? 'Yes' : 'No'}</Typography>

                    <Typography variant="h6" sx={{color: '#3b82f6', mt: 1}}>LLM Model:</Typography>
                    <Typography variant="body1">{exp.llmModel}</Typography>
                    
                    <Typography variant="h6" sx={{color: '#3b82f6', mt: 1}}>Reference Number: </Typography>
                    <Typography variant="body1">{exp.refNum ? exp.refNum : 'Null'}</Typography>
                    
                    <Typography variant="h6" sx={{color: '#3b82f6', mt: 1}}>Reviewer Round:</Typography>
                    <Typography variant="body1">{exp.reviewerRound ? exp.reviewerRound : 'Null'}</Typography>
                </Box>

                <Box
                    sx={{
                        width: '70vw', // 设置右侧内容宽度
                        backgroundColor: '#fff',
                        overflowY: 'auto',
                        height: '78vh', // 保证右侧区域适应高度
                        maxHeight: '78vh',
                    }}
                >
                    {/* 右侧具体内容 */}
                    <Outlet />
                </Box>
            </Box>
        </Box>
    );
}
