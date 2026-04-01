import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import ProgramContent from '../../components/ProgramContent';
import { useParams } from 'react-router-dom';
import {
  getCompletedSteps,
  getProgram,
  getProgramMeta,
  regenerateProgram,
  regenerateProgramWithFeedback,
  downloadProgramDataZip,
} from '../../services/api';
import ErrorPage from '../../components/ErrorPage';

function CustomTabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

CustomTabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired,
};

function a11yProps(index) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

const phaseLabelMap = {
  coding_preflight_start: '预检中：正在检查任务所需输入与数据可用性...',
  coding_preflight_done: '预检完成：任务输入已锁定，开始规划与执行...',
  coding_preflight_blocked: '预检阻断：存在任务缺少输入文件，请先补齐数据。',
  coding_preflight_incomplete: '预检不完整：仍有必需数据未下载完成。',
  coding_planning_start: 'Planning with gpt-5.2-thinking...',
  coding_planning_done: 'Plan ready, starting execution with gpt-5.2-codex...',
  coding_task_start: 'Preparing current task...',
  coding_primary_execute_start: 'Generating and executing code with gpt-5.2-codex...',
  coding_retry_diag_5_2_thinking: 'Diagnosing failure with gpt-5.2-thinking...',
  coding_retry_execute_5_3_codex: 'Retrying with gpt-5.3-codex...',
  coding_task_done: 'Task completed, moving to next task...',
  coding_task_failed_final_chain: 'Escalation chain failed for current task.',
  coding_wait_user_feedback: 'Paused: waiting for your feedback before retry.',
  coding_failed_final: 'Project failed after feedback retry. Please restart.',
};

const isCodingCheckpoint = (cp) => (cp || '').toLowerCase().startsWith('coding_');
const MAX_INLINE_FULL_BYTES = 2 * 1024 * 1024;
const asErrorMessage = (err) => {
  const detail = err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message;
  if (typeof detail === 'string') return detail;
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail || 'Unknown error');
  }
};

export default function Programming() {
  const { id } = useParams();
  const isExampleProject = Number(id) === 94127;

  const [versions, setVersions] = React.useState([1]);
  const [selectedVersion, setSelectedVersion] = React.useState(1);
  const [content, setContent] = React.useState(null);
  const [contentError, setContentError] = React.useState(null);
  const [programNotReady, setProgramNotReady] = React.useState(false);

  const [regenerating, setRegenerating] = React.useState(false);
  const [regenMessage, setRegenMessage] = React.useState('');
  const [feedbackOpen, setFeedbackOpen] = React.useState(false);
  const [feedbackText, setFeedbackText] = React.useState('');
  const [pendingFeedbackInfo, setPendingFeedbackInfo] = React.useState(null);

  const [runtimeStatus, setRuntimeStatus] = React.useState({
    checkpoint: 'init',
    message: 'Idle',
    running: false,
  });

  const [globalPlan, setGlobalPlan] = React.useState('');
  const [taskProgress, setTaskProgress] = React.useState({
    total_tasks: 0,
    completed_tasks: 0,
    failed_tasks: 0,
    remaining_tasks: 0,
    completed_task_ids: [],
    failed_task_ids: [],
    pending_task_ids: [],
  });
  const [generatedFiles, setGeneratedFiles] = React.useState([]);
  const [displayFiles, setDisplayFiles] = React.useState([]);
  const [displayItems, setDisplayItems] = React.useState([]);
  const [showDoneTasks, setShowDoneTasks] = React.useState(false);
  const [downloadingZip, setDownloadingZip] = React.useState(false);
  const [showFullData, setShowFullData] = React.useState(false);
  const [fullDataMap, setFullDataMap] = React.useState({});
  const [fullDataLoadingMap, setFullDataLoadingMap] = React.useState({});
  const [imagePreview, setImagePreview] = React.useState({ open: false, name: '', src: '' });

  const fetchVersions = React.useCallback(async () => {
    try {
      const res = await getCompletedSteps(id);
      const payload = res.data || {};
      setRuntimeStatus({
        checkpoint: payload.checkpoint || 'init',
        message: payload.message || 'Idle',
        running: Boolean(payload.running),
      });
      const available = Array.isArray(payload.coding_available_versions)
        ? payload.coding_available_versions.filter((v) => Number.isInteger(v) && v > 0)
        : [];
      const nextVersions = available.length > 0 ? available : [1];
      setVersions(nextVersions);
      if (!nextVersions.includes(selectedVersion)) {
        setSelectedVersion(nextVersions[0]);
      }
    } catch {
      setVersions([1]);
      setSelectedVersion(1);
    }
  }, [id, selectedVersion]);

  const fetchProgram = React.useCallback(async () => {
    try {
      const res = await getProgram(id, selectedVersion - 1);
      if (res?.data?.not_ready) {
        setContent(null);
        setContentError(null);
        setProgramNotReady(true);
        return;
      }
      setContent(<ProgramContent data={res.data} />);
      setContentError(null);
      setProgramNotReady(false);
    } catch (err) {
      const code = err?.response?.status || err?.status || 500;
      if (code === 404) {
        setContent(null);
        setContentError(null);
        setProgramNotReady(true);
        return;
      }
      setContent(
        <ErrorPage
          code={code}
          message={asErrorMessage(err)}
        />
      );
      setContentError(code);
      setProgramNotReady(false);
    }
  }, [id, selectedVersion]);

  const fetchProgramMeta = React.useCallback(async () => {
    try {
      const res = await getProgramMeta(id);
      const gp = res?.data?.global_plan?.plan;
      setGlobalPlan(typeof gp === 'string' ? gp : '');
      setTaskProgress({
        total_tasks: Number(res?.data?.task_progress?.total_tasks || 0),
        completed_tasks: Number(res?.data?.task_progress?.completed_tasks || 0),
        failed_tasks: Number(res?.data?.task_progress?.failed_tasks || 0),
        remaining_tasks: Number(res?.data?.task_progress?.remaining_tasks || 0),
        completed_task_ids: Array.isArray(res?.data?.task_progress?.completed_task_ids)
          ? res.data.task_progress.completed_task_ids
          : [],
        failed_task_ids: Array.isArray(res?.data?.task_progress?.failed_task_ids)
          ? res.data.task_progress.failed_task_ids
          : [],
        pending_task_ids: Array.isArray(res?.data?.task_progress?.pending_task_ids)
          ? res.data.task_progress.pending_task_ids
          : [],
      });
      setGeneratedFiles(Array.isArray(res?.data?.generated_files) ? res.data.generated_files : []);
      setDisplayFiles(Array.isArray(res?.data?.display_files) ? res.data.display_files : []);
      setDisplayItems(Array.isArray(res?.data?.display_items) ? res.data.display_items : []);
    } catch {
      setGlobalPlan('');
    }
  }, [id]);

  const handleDownloadZip = async () => {
    setDownloadingZip(true);
    try {
      const res = await downloadProgramDataZip(id);
      const blob = new Blob([res.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const now = new Date();
      const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
      a.download = `experiment_${id}_data_${stamp}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setRegenMessage('Display data package downloaded (charts + R code + manifest).');
    } catch (err) {
      setRegenMessage(`Display data package download failed: ${asErrorMessage(err)}`);
    } finally {
      setDownloadingZip(false);
    }
  };

  React.useEffect(() => {
    fetchVersions();
    fetchProgramMeta();
    fetchProgram();
  }, [fetchVersions, fetchProgramMeta, fetchProgram]);

  React.useEffect(() => {
    const timer = setInterval(() => {
      fetchVersions();
      fetchProgramMeta();
      fetchProgram();
    }, 1500);
    return () => clearInterval(timer);
  }, [fetchVersions, fetchProgramMeta, fetchProgram]);

  const handleChange = (event, newValue) => {
    const nextVersion = versions[newValue];
    if (nextVersion !== undefined) {
      setSelectedVersion(nextVersion);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    setRegenMessage('');
    try {
      await regenerateProgram(id);
      setRegenMessage('Coding regenerated successfully.');
      await fetchVersions();
      await fetchProgramMeta();
      await fetchProgram();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409 && detail?.needs_user_feedback) {
        setPendingFeedbackInfo(detail);
        setFeedbackOpen(true);
        setRegenMessage('Escalation chain failed once. Please provide feedback to continue.');
      } else if (err?.response?.status === 422 && detail?.project_failed) {
        setRegenMessage(detail?.message || 'Project failed. Please restart.');
      } else {
        setRegenMessage(detail || 'Regeneration failed.');
      }
    } finally {
      setRegenerating(false);
    }
  };

  const handleSubmitFeedbackRetry = async () => {
    if (!feedbackText.trim()) {
      setRegenMessage('Please input your feedback first.');
      return;
    }
    setRegenerating(true);
    try {
      await regenerateProgramWithFeedback(id, feedbackText.trim());
      setRegenMessage('Coding regenerated successfully after feedback.');
      setFeedbackOpen(false);
      setFeedbackText('');
      setPendingFeedbackInfo(null);
      await fetchVersions();
      await fetchProgramMeta();
      await fetchProgram();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 422 && detail?.project_failed) {
        setRegenMessage(detail?.message || 'Second retry still failed. Please restart project.');
        setFeedbackOpen(false);
      } else {
        setRegenMessage(detail || 'Feedback retry failed.');
      }
    } finally {
      setRegenerating(false);
    }
  };

  const tabValue = Math.max(0, versions.indexOf(selectedVersion));
  const runtimePhaseLabel = phaseLabelMap[runtimeStatus.checkpoint] || runtimeStatus.message || 'Idle';
  const showSpinnerPanel = programNotReady && (runtimeStatus.running || isCodingCheckpoint(runtimeStatus.checkpoint));
  const orderedTaskIds = React.useMemo(() => {
    const all = [
      ...(Array.isArray(taskProgress.completed_task_ids) ? taskProgress.completed_task_ids : []),
      ...(Array.isArray(taskProgress.failed_task_ids) ? taskProgress.failed_task_ids : []),
      ...(Array.isArray(taskProgress.pending_task_ids) ? taskProgress.pending_task_ids : []),
    ];
    return Array.from(new Set(all));
  }, [taskProgress]);
  const nonDoneTaskIds = React.useMemo(
    () => orderedTaskIds.filter((taskId) => !taskProgress.completed_task_ids.includes(taskId)),
    [orderedTaskIds, taskProgress.completed_task_ids]
  );
  const outputFileUrl = React.useCallback(
    (name) => `/api/${id}/program/output-file?name=${encodeURIComponent(name)}`,
    [id]
  );

  const fetchFullData = React.useCallback(async (item) => {
    const name = item?.name;
    if (!name) return;
    if (fullDataMap[name] || fullDataLoadingMap[name]) return;
    if (Number(item?.size_bytes || 0) > MAX_INLINE_FULL_BYTES) {
      setFullDataMap((prev) => ({
        ...prev,
        [name]: { tooLarge: true, message: 'File is too large for inline full rendering. Please click Open.' },
      }));
      return;
    }

    setFullDataLoadingMap((prev) => ({ ...prev, [name]: true }));
    try {
      const res = await fetch(outputFileUrl(name));
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const rt = item?.render_type || 'download';
      if (rt === 'json') {
        const j = await res.json();
        setFullDataMap((prev) => ({ ...prev, [name]: { kind: 'json', data: j } }));
      } else if (rt === 'table') {
        const txt = await res.text();
        const lower = String(name).toLowerCase();
        const delim = lower.endsWith('.tsv') ? '\t' : ',';
        const rows = txt.split(/\r?\n/).filter((x) => x.length > 0).map((line) => line.split(delim));
        setFullDataMap((prev) => ({ ...prev, [name]: { kind: 'table', data: rows } }));
      } else if (rt === 'text') {
        const txt = await res.text();
        setFullDataMap((prev) => ({ ...prev, [name]: { kind: 'text', data: txt } }));
      } else {
        setFullDataMap((prev) => ({ ...prev, [name]: { kind: 'unsupported' } }));
      }
    } catch (e) {
      setFullDataMap((prev) => ({
        ...prev,
        [name]: { error: true, message: String(e?.message || e || 'Failed to load full data') },
      }));
    } finally {
      setFullDataLoadingMap((prev) => ({ ...prev, [name]: false }));
    }
  }, [fullDataMap, fullDataLoadingMap, outputFileUrl]);

  React.useEffect(() => {
    if (!showFullData) return;
    displayItems.forEach((item) => {
      if (!item) return;
      const rt = item?.render_type;
      if (rt === 'table' || rt === 'json' || rt === 'text') {
        fetchFullData(item);
      }
    });
  }, [showFullData, displayItems, fetchFullData]);

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleChange} aria-label="coding tabs" centered>
          {versions.map((version, index) => (
            <Tab
              key={version}
              label={`coding${version}`}
              sx={{ textTransform: 'none' }}
              {...a11yProps(index)}
            />
          ))}
        </Tabs>
        <Stack direction="row" spacing={1} justifyContent="center" sx={{ pb: 1 }}>
          {!isExampleProject ? (
            <Button
              variant="outlined"
              onClick={handleRegenerate}
              disabled={regenerating}
              sx={{ textTransform: 'none' }}
            >
              {regenerating ? 'Regenerating coding...' : 'Regenerate coding'}
            </Button>
          ) : null}
          <Button
            variant="contained"
            onClick={handleDownloadZip}
            disabled={downloadingZip}
            sx={{ textTransform: 'none' }}
          >
            {downloadingZip ? 'Preparing display package...' : 'Download Display Data Package'}
          </Button>
        </Stack>
        <Box sx={{ px: 2, pb: 1 }}>
          <Alert severity="info">
            Download package includes displayed result files, R code, and a manifest JSON.
          </Alert>
        </Box>
        {regenMessage ? (
          <Box sx={{ px: 2, pb: 1 }}>
            <Alert severity={regenMessage.toLowerCase().includes('failed') ? 'error' : 'success'}>
              {regenMessage}
            </Alert>
          </Box>
        ) : null}
        <Box sx={{ px: 2, pb: 1 }}>
          <Alert severity={runtimeStatus.running ? 'info' : 'success'}>
            {runtimePhaseLabel}
          </Alert>
        </Box>
      </Box>

      <Box sx={{ width: '70vw', ml: 'auto', mr: 'auto', mt: '2vh' }}>
        <Box sx={{ mb: 2, p: 2, borderRadius: 1, border: '1px solid #e0e0e0', backgroundColor: '#fafafa' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Task Progress
          </Typography>
          <Typography variant="body2">
            Total: {taskProgress.total_tasks} | Completed: {taskProgress.completed_tasks} | Failed: {taskProgress.failed_tasks} | Remaining: {taskProgress.remaining_tasks}
          </Typography>
          {taskProgress.remaining_tasks > 0 ? (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2">Running... {taskProgress.remaining_tasks} task(s) still pending</Typography>
            </Stack>
          ) : null}
          {nonDoneTaskIds.length > 0 ? (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Active/Failed task details</Typography>
              <Stack spacing={0.8} sx={{ mt: 0.8 }}>
                {nonDoneTaskIds.map((taskId) => {
                  const isFailed = taskProgress.failed_task_ids.includes(taskId);
                  const isPending = taskProgress.pending_task_ids.includes(taskId);
                  return (
                    <Stack key={taskId} direction="row" spacing={1} alignItems="center">
                      {isPending ? <CircularProgress size={14} /> : <Box sx={{ width: 14 }} />}
                      <Typography variant="body2" sx={{ flex: 1 }}>
                        {taskId}
                      </Typography>
                      {isPending ? <Chip size="small" color="info" label="Running" /> : null}
                      {isFailed ? <Chip size="small" color="error" label="Failed" /> : null}
                    </Stack>
                  );
                })}
              </Stack>
            </Box>
          ) : null}
          {taskProgress.completed_task_ids.length > 0 ? (
            <Box sx={{ mt: 1 }}>
              <Button
                size="small"
                variant="text"
                onClick={() => setShowDoneTasks((v) => !v)}
                sx={{ textTransform: 'none', pl: 0 }}
              >
                {showDoneTasks ? 'Hide Done tasks' : `Show Done tasks (${taskProgress.completed_task_ids.length})`}
              </Button>
              <Collapse in={showDoneTasks}>
                <Stack spacing={0.6} sx={{ mt: 0.8 }}>
                  {taskProgress.completed_task_ids.map((taskId) => (
                    <Stack key={`done-${taskId}`} direction="row" spacing={1} alignItems="center">
                      <Box sx={{ width: 14 }} />
                      <Typography variant="body2" sx={{ flex: 1 }}>{taskId}</Typography>
                      <Chip size="small" color="success" label="Done" />
                    </Stack>
                  ))}
                </Stack>
              </Collapse>
            </Box>
          ) : null}
          {displayItems.length > 0 ? (
            <Box sx={{ mt: 1 }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Typography variant="body2" sx={{ fontWeight: 600 }}>Result previews</Typography>
                <FormControlLabel
                  control={
                    <Switch
                      size="small"
                      checked={showFullData}
                      onChange={(e) => setShowFullData(e.target.checked)}
                    />
                  }
                  label={showFullData ? 'Full Data View: ON' : 'Full Data View: OFF'}
                />
              </Stack>
              <Stack spacing={1} sx={{ mt: 0.8 }}>
                {displayItems.map((item) => {
                  const name = item?.name || 'unknown';
                  const renderType = item?.render_type || 'download';
                  const full = fullDataMap[name];
                  const loadingFull = Boolean(fullDataLoadingMap[name]);
                  return (
                    <Box key={`preview-${name}`} sx={{ p: 1.2, border: '1px solid #e0e0e0', borderRadius: 1, backgroundColor: '#fff' }}>
                      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.8 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, flex: 1 }}>{name}</Typography>
                        <Chip size="small" color="primary" label={renderType} />
                        <Button
                          size="small"
                          variant="outlined"
                          sx={{ textTransform: 'none' }}
                          component="a"
                          href={outputFileUrl(name)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </Button>
                      </Stack>
                      {renderType === 'table' && Array.isArray(item?.table_preview) ? (
                        <Box sx={{ overflowX: 'auto', maxHeight: 240, border: '1px solid #f0f0f0' }}>
                          <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                            <tbody>
                              {(showFullData && full?.kind === 'table' && Array.isArray(full?.data) ? full.data : item.table_preview).map((row, idx) => (
                                <tr key={`${name}-row-${idx}`}>
                                  {(Array.isArray(row) ? row : []).map((cell, cidx) => (
                                    <td key={`${name}-cell-${idx}-${cidx}`} style={{ border: '1px solid #eee', padding: '4px 6px', fontSize: 12 }}>
                                      {String(cell ?? '')}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </Box>
                      ) : null}
                      {renderType === 'json' && item?.json_preview !== undefined ? (
                        <Box sx={{ maxHeight: 260, overflowY: 'auto', backgroundColor: '#fafafa', p: 1, borderRadius: 1, whiteSpace: 'pre-wrap', fontSize: 12 }}>
                          {JSON.stringify(showFullData && full?.kind === 'json' ? full.data : item.json_preview, null, 2)}
                        </Box>
                      ) : null}
                      {renderType === 'text' && typeof item?.text_preview === 'string' ? (
                        <Box sx={{ maxHeight: 260, overflowY: 'auto', backgroundColor: '#fafafa', p: 1, borderRadius: 1, whiteSpace: 'pre-wrap', fontSize: 12 }}>
                          {showFullData && full?.kind === 'text' ? full.data : item.text_preview}
                        </Box>
                      ) : null}
                      {showFullData && (renderType === 'table' || renderType === 'json' || renderType === 'text') ? (
                        <Box sx={{ mt: 0.6 }}>
                          {loadingFull ? <Typography variant="caption">Loading full data...</Typography> : null}
                          {full?.tooLarge ? <Typography variant="caption" color="warning.main">{full.message}</Typography> : null}
                          {full?.error ? <Typography variant="caption" color="error.main">{full.message}</Typography> : null}
                        </Box>
                      ) : null}
                      {renderType === 'image' ? (
                        <Box sx={{ maxHeight: 320, overflow: 'auto' }}>
                          <img
                            src={outputFileUrl(name)}
                            alt={name}
                            onClick={() => setImagePreview({ open: true, name, src: outputFileUrl(name) })}
                            style={{ maxWidth: '100%', display: 'block', cursor: 'zoom-in' }}
                          />
                        </Box>
                      ) : null}
                    </Box>
                  );
                })}
              </Stack>
            </Box>
          ) : null}
          {generatedFiles.length > 0 && displayItems.length === 0 ? (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Generated files</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {(displayFiles.length > 0 ? displayFiles : generatedFiles).join('\n')}
              </Typography>
            </Box>
          ) : null}
        </Box>

        {globalPlan ? (
          <Box sx={{ mb: 2 }}>
            <Alert severity="info" sx={{ mb: 1 }}>
              Global Plan (gpt-5.2-thinking)
            </Alert>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid #e0e0e0',
                backgroundColor: '#fafafa',
                maxHeight: '22vh',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                fontSize: 13,
              }}
            >
              {globalPlan}
            </Box>
          </Box>
        ) : null}

        <Divider sx={{ mb: 2 }} />
      </Box>

      <Box
        sx={{
          height: '62vh',
          maxHeight: '66vh',
          overflowY: 'auto',
          width: '70vw',
          ml: 'auto',
          mr: 'auto',
          mt: '1vh',
          borderRadius: '8px',
          boxShadow: 3,
        }}
      >
        <CustomTabPanel value={tabValue} index={tabValue}>
          {showSpinnerPanel ? (
            <Box sx={{ py: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <CircularProgress />
              <Typography variant="body1">Code is being generated and executed...</Typography>
              <Typography variant="body2">
                Completed {taskProgress.completed_tasks}/{taskProgress.total_tasks}, remaining {taskProgress.remaining_tasks}
              </Typography>
            </Box>
          ) : null}

          {!showSpinnerPanel && programNotReady && !runtimeStatus.running ? (
            <Alert severity="info">No code files generated yet for this version.</Alert>
          ) : null}

          {!programNotReady && content ? content : null}
          {!showSpinnerPanel && contentError && !content ? <ErrorPage code={contentError} message="Failed to load code content." /> : null}
        </CustomTabPanel>
      </Box>

      <Dialog open={feedbackOpen} onClose={() => setFeedbackOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Feedback Required</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            {pendingFeedbackInfo?.message || 'Coding failed after escalation. Please provide your guidance.'}
          </Alert>
          {pendingFeedbackInfo?.failed_task_id ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              Failed task: {pendingFeedbackInfo.failed_task_id}
            </Alert>
          ) : null}
          <TextField
            label="Your feedback"
            multiline
            minRows={5}
            fullWidth
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Example: use local cached dataset only; avoid online query; enforce fixed output filenames..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackOpen(false)} disabled={regenerating}>Cancel</Button>
          <Button onClick={handleSubmitFeedbackRetry} variant="contained" disabled={regenerating}>
            Submit and Retry
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={imagePreview.open}
        onClose={() => setImagePreview({ open: false, name: '', src: '' })}
        maxWidth="xl"
        fullWidth
      >
        <DialogTitle sx={{ pr: 6 }}>
          {imagePreview.name || 'Image Preview'}
          <IconButton
            aria-label="close"
            onClick={() => setImagePreview({ open: false, name: '', src: '' })}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', justifyContent: 'center', backgroundColor: '#111' }}>
          {imagePreview.src ? (
            <img
              src={imagePreview.src}
              alt={imagePreview.name || 'preview'}
              style={{ maxWidth: '100%', maxHeight: '80vh', display: 'block' }}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
