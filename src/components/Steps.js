import * as React from 'react';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepButton from '@mui/material/StepButton';
import { useNavigate, useParams } from 'react-router-dom';
import { Outlet } from 'react-router-dom';

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
                        <Step key={label}>
                            <StepButton
                                color="inherit"
                                onClick={handleStep(index)}
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
                overflowY: 'auto',
                height: '78vh',
                maxHeight: '78vh',
                borderRadius: '8px',
                margin: 'auto',
                mt: '2vh',
                mr: '4vw',
                ml: '4vw',
            }}>
               <Outlet/> 
            </Box>
        </Box>
    );
}
