import * as React from 'react';
import { useState, useEffect, useMemo, useCallback } from 'react';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepButton from '@mui/material/StepButton';
import StepLabel from '@mui/material/StepLabel';
import { useNavigate, useParams, useLocation, useBeforeUnload } from 'react-router-dom';
import { Outlet } from 'react-router-dom';
import { getCompletedSteps, getProject, resumeExperiment, pauseExperiment } from '../services/api';
import { Typography, LinearProgress, CircularProgress } from '@mui/material';

const steps = [
  'Search',
  'Literature Processing',
  'Experimental Design',
  'Dry Experiments',
  'Programming',
];

const stepRoutes = [
  'search',
  'literature-processing',
  'experimental-design',
  'dry-experiments',
  'programming',
];

const checkpointToStep = (checkpoint) => {
  const cp = (checkpoint || '').toLowerCase();
  if (cp.startsWith('search_') || ['start', 'queued', 'prepare_dirs'].includes(cp)) return 0;
  if (cp.startsWith('literature')) return 1;
  if (cp.startsWith('design_')) return 2;
  if (cp.startsWith('dry_')) return 3;
  if (cp.startsWith('coding_')) return 4;
  return null;
};

const isResumeBlockedCheckpoint = (checkpoint) => {
  const cp = (checkpoint || '').toLowerCase();
  if (cp === 'coding_wait_user_feedback' || cp === 'coding_failed_final' || cp === 'pause_requested' || cp === 'paused_by_user') {
    return true;
  }
  // Do not auto-resume once programming has completed; restart should be user-triggered (regenerate).
  if (cp === 'done' || cp === 'coding_v3_done') {
    return true;
  }
  return false;
};

export default function HorizontalLinearAlternativeLabelStepper() {
  const [activeStep, setActiveStep] = React.useState(0);
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const [completedSteps, setCompletedSteps] = useState([]);
  const [exp, setExp] = useState();
  const [runtimeStatus, setRuntimeStatus] = useState({
    running: false,
    progress: 0,
    message: 'Idle',
    checkpoint: 'init',
    error: null,
    stage_progresses: [0, 0, 0, 0, 0],
    running_stage: null,
  });
  const resumeCooldownRef = React.useRef(0);
  const latestRunningRef = React.useRef(false);
  const leavePromptHandledRef = React.useRef(false);

  const runningStep = useMemo(() => {
    if (!runtimeStatus.running) return null;
    if (runtimeStatus.running_stage !== null && runtimeStatus.running_stage !== undefined) {
      return runtimeStatus.running_stage;
    }
    for (let i = 0; i < steps.length; i += 1) {
      if (!completedSteps.includes(i)) return i;
    }
    return null;
  }, [runtimeStatus.running, runtimeStatus.running_stage, completedSteps]);

  const displayStep = useMemo(() => {
    if (runtimeStatus.running && runningStep !== null && runningStep !== undefined) {
      return runningStep;
    }
    const checkpointStep = checkpointToStep(runtimeStatus.checkpoint);
    if (checkpointStep !== null && checkpointStep !== undefined) {
      return checkpointStep;
    }
    return activeStep;
  }, [runtimeStatus.running, runningStep, runtimeStatus.checkpoint, activeStep]);

  const displayStageProgress = useMemo(() => {
    const arr = runtimeStatus.stage_progresses || [0, 0, 0, 0, 0];
    const val = Number(arr[displayStep] || 0);
    return Math.max(0, Math.min(100, val));
  }, [runtimeStatus.stage_progresses, displayStep]);

  const unlockedSteps = useMemo(() => {
    const unlocked = new Set([0]);
    completedSteps.forEach((step) => {
      unlocked.add(step);
      if (step + 1 < steps.length) {
        unlocked.add(step + 1);
      }
    });
    return Array.from(unlocked).sort((a, b) => a - b);
  }, [completedSteps]);

  const handleStep = (step) => () => {
    setActiveStep(step);
    navigate(`/${id}/steps/${stepRoutes[step]}`, { replace: false });
  };

  const fetchStepsCompleted = useCallback(async () => {
    try {
      const response = await getCompletedSteps(id);
      const payload = response.data;
      if (Array.isArray(payload)) {
        setCompletedSteps(payload);
        setRuntimeStatus((prev) => ({ ...prev }));
      } else {
        setCompletedSteps(payload.completed_steps || []);
        setRuntimeStatus({
          running: Boolean(payload.running),
          progress: Number(payload.progress || 0),
          message: payload.message || 'Idle',
          checkpoint: payload.checkpoint || 'init',
          error: payload.error || null,
          stage_progresses: Array.isArray(payload.stage_progresses) ? payload.stage_progresses : [0, 0, 0, 0, 0],
          running_stage: payload.running_stage ?? null,
        });
      }
    } catch (error) {
      console.log(error);
    }
  }, [id]);

  const fetchProject = useCallback(async () => {
    try {
      const response = await getProject(id);
      setExp(response.data);
    } catch (error) {
      console.log(error);
    }
  }, [id]);

  useEffect(() => {
    fetchStepsCompleted();
    fetchProject();
  }, [id, fetchStepsCompleted, fetchProject]);

  useEffect(() => {
    let mounted = true;
    const tick = async () => {
      if (!mounted) return;
      await fetchStepsCompleted();
    };

    const interval = setInterval(tick, 1000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [id, fetchStepsCompleted]);

  useEffect(() => {
    const allDone = completedSteps.length === steps.length;
    if (allDone || runtimeStatus.running || isResumeBlockedCheckpoint(runtimeStatus.checkpoint)) {
      return;
    }

    const now = Date.now();
    if (now - resumeCooldownRef.current < 10000) {
      return;
    }
    resumeCooldownRef.current = now;

    resumeExperiment(id)
      .then(() => {
        fetchStepsCompleted();
      })
      .catch(() => {});
  }, [id, completedSteps, runtimeStatus.running, runtimeStatus.checkpoint, fetchStepsCompleted]);

  useEffect(() => {
    const currentRoute = location.pathname.split('/').pop();
    const currentIndex = stepRoutes.indexOf(currentRoute);
    if (currentIndex >= 0) {
      setActiveStep(currentIndex);
      return;
    }
  }, [location.pathname]);

  useEffect(() => {
    latestRunningRef.current = Boolean(runtimeStatus.running);
  }, [runtimeStatus.running]);

  useEffect(() => {
    return () => {
      if (leavePromptHandledRef.current || !latestRunningRef.current) return;
      leavePromptHandledRef.current = true;
      const keepRunning = window.confirm(
        'Project is running.\nOK: leave and keep running in background.\nCancel: pause project in backend.'
      );
      if (!keepRunning) {
        pauseExperiment(id).catch(() => {});
      }
    };
  }, [id]);

  useBeforeUnload(
    React.useCallback(
      (event) => {
        if (!runtimeStatus.running) return;
        event.preventDefault();
        event.returnValue = '';
      },
      [runtimeStatus.running]
    )
  );

  if (!exp) {
    return <Box sx={{ height: '90vh' }}></Box>;
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
          sx={{
            height: '6vh',
            backgroundColor: '#fff',
            borderRadius: '8px',
            padding: '16px',
            boxShadow: 2,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            width: '70%',
          }}
        >
          {steps.map((label, index) => (
            <Step key={label} completed={completedSteps.includes(index)}>
              <StepButton
                color="inherit"
                onClick={handleStep(index)}
                disabled={!unlockedSteps.includes(index)}
                sx={{
                  height: '4vh',
                }}
              >
                <StepLabel
                  {...(
                    runningStep === index && !completedSteps.includes(index)
                      ? { icon: <CircularProgress size={18} thickness={5} /> }
                      : {}
                  )}
                >
                  {label}
                </StepLabel>
              </StepButton>
            </Step>
          ))}
        </Stepper>
      </Box>

      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mt: 2,
          mx: '5vw',
        }}
      >
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
          <Typography variant="h5" align="center" sx={{ mt: '2vh', mb: '2vh', color: '#2274f2', fontWeight: 'bold' }}>
            Task Information
          </Typography>

          <Typography variant="h6" sx={{ color: '#3b82f6' }}>
            Experiment Name:
          </Typography>
          <Typography variant="body1">{exp.expName}</Typography>

          <Typography variant="h6" sx={{ color: '#3b82f6', mt: 1 }}>
            Experiment Purpose:
          </Typography>
          <Typography variant="body1">{exp.expPurpose}</Typography>

          <Typography variant="h6" sx={{ color: '#3b82f6', mt: 1 }}>
            Experiment Condition:
          </Typography>
          <Typography variant="body1">{exp.expCondition}</Typography>

          <Typography variant="h6" sx={{ color: '#3b82f6', mt: 1 }}>
            Current Stage Progress:
          </Typography>
          <LinearProgress variant="determinate" value={displayStageProgress} sx={{ mt: 1, mb: 1 }} />
          <Typography variant="body2">{`Stage: ${steps[displayStep]}`}</Typography>
          <Typography variant="body2">{`Progress: ${displayStageProgress}%`}</Typography>
          <Typography variant="body2">{`Status: ${runtimeStatus.message || 'Idle'}`}</Typography>
          {runtimeStatus.error && (
            <Typography variant="body2" color="error">{`Error: ${runtimeStatus.error}`}</Typography>
          )}
        </Box>

        <Box
          sx={{
            width: '70vw',
            backgroundColor: '#fff',
            overflowY: 'auto',
            height: '78vh',
            maxHeight: '78vh',
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
