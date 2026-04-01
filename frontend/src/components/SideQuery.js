import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { useState, useEffect, useCallback } from 'react';
import { getPapersets, getDatasets, getCompletedSteps, uploadManualPaperPdf } from '../services/api';
import { useParams } from 'react-router-dom';
import PapersView from './PapersView';
import DatasetsView from './DatasetsView';
import { PieChart } from '@mui/x-charts/PieChart';
import LoadingProgress from './LoadingProgress';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';


function TabPanel(props) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`vertical-tabpanel-${index}`}
            aria-labelledby={`vertical-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    <Typography>{children}</Typography>
                </Box>
            )}
        </div>
    );
}

TabPanel.propTypes = {
    children: PropTypes.node,
    index: PropTypes.number.isRequired,
    value: PropTypes.number.isRequired,
};

function a11yProps(index) {
    return {
        id: `vertical-tab-${index}`,
        'aria-controls': `vertical-tabpanel-${index}`,
    };
}

export default function VerticalTabs({ type }) {
    const [value, setValue] = useState(0);
    const [data, setData] = useState();
    const [pieData, setPieData] = useState([]);
    const [pending, setPending] = useState(true);
    const [runtimeProgress, setRuntimeProgress] = useState(0);
    const [runtimeMessage, setRuntimeMessage] = useState('');
    const [manualUploadNeeded, setManualUploadNeeded] = useState([]);
    const [manualDialogOpen, setManualDialogOpen] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState({});
    const { id } = useParams();
    const isExampleProject = Number(id) === 94127;
    const [uploadingUid, setUploadingUid] = useState('');
    const [uploadError, setUploadError] = useState('');
    const dismissKey = React.useMemo(() => `manualUploadDismissed_${id}`, [id]);
    const maxLabelLength = 40;
    const fetchPapersets = useCallback(async () => {
        try {
            const response = await getPapersets(id);
            setData(response.data.retrieved_papers);
            setPieData(response.data.count);
            setPending(Boolean(response.data.pending));
            const needs = response.data.manual_upload_needed || [];
            setManualUploadNeeded(needs);
            const dismissed = sessionStorage.getItem(dismissKey) === '1';
            if (needs.length > 0 && !dismissed && !isExampleProject) {
                setManualDialogOpen(true);
            }
        }
        catch (error) {
            console.log(error);
            setPending(false);
        }
    }, [id, dismissKey, isExampleProject]);

    const fetchDatasets = useCallback(async () => {
        try {
            const response = await getDatasets(id);
            const payload = response.data || {};
            const { pending: pendingFlag, ...datasetGroups } = payload;
            setData(datasetGroups);
            setPending(Boolean(pendingFlag));
        }
        catch (error) {
            console.log(error);
            setPending(false);
        }
    }, [id]);

    useEffect(() => {
        setPending(true);
        if (isExampleProject) {
            setManualDialogOpen(false);
        }
        if (type === 'papers') {
            fetchPapersets();
        } else {
            fetchDatasets();
        }
    }, [type, fetchPapersets, fetchDatasets, isExampleProject])

    useEffect(() => {
        if (!pending) return undefined;
        const tick = async () => {
            try {
                const response = await getCompletedSteps(id);
                const payload = response.data;
                if (!Array.isArray(payload)) {
                    const stageProgress = Array.isArray(payload.stage_progresses) ? Number(payload.stage_progresses[0] || 0) : Number(payload.progress || 0);
                    setRuntimeProgress(stageProgress);
                    setRuntimeMessage(payload.message || '');
                }
            } catch (error) {
                // ignore transient poll errors
            }
        };
        tick();
        const timer = setInterval(tick, 1500);
        return () => clearInterval(timer);
    }, [id, pending]);

    // 截断标签文本，省略号
    const truncateLabel = (label) => {
        if (label.length > maxLabelLength) {
            return label.slice(0, maxLabelLength) + '...';
        }
        return label;
    };

    const handleChange = (event, newValue) => {
        setValue(newValue);
    };

    const handleSelectFile = (uid, event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        setSelectedFiles((prev) => ({ ...prev, [uid]: file }));
    };

    const handleManualUpload = async (paper) => {
        const file = selectedFiles[paper.uid];
        if (!file) {
            setUploadError('Please choose a PDF file first.');
            return;
        }
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            setUploadError('Only PDF files are supported.');
            return;
        }
        try {
            setUploadError('');
            setUploadingUid(paper.uid);
            const formData = new FormData();
            formData.append('file', file);
            formData.append('doi', paper.doi || '');
            formData.append('pmcid', paper.pmcid || '');
            formData.append('title', paper.title || '');
            const response = await uploadManualPaperPdf(id, formData);
            setManualUploadNeeded(response.data.manual_upload_needed || []);
            sessionStorage.removeItem(dismissKey);
            setSelectedFiles((prev) => {
                const next = { ...prev };
                delete next[paper.uid];
                return next;
            });
            await fetchPapersets();
        } catch (error) {
            setUploadError(error?.response?.data?.detail || 'Upload failed.');
        } finally {
            setUploadingUid('');
        }
    };

    const loadingLabel = type === 'papers' ? 'Loading paper source...' : 'Loading dataset source...';

    if (!data || pending) {
        return (
            <LoadingProgress
                label={loadingLabel}
                progressValue={runtimeProgress}
                detail={runtimeMessage}
                stepPercent={5}
            />
        );
    }
    const scoreData = [
        { score: 1, color: '#FF0000' },  // 红
        { score: 2, color: '#FF8000' },  // 橙
        { score: 3, color: '#FFFF00' },  // 黄
        { score: 4, color: '#80FF00' },  // 绿
        { score: 5, color: '#00FF00' },  // 深绿
      ];
    let chartData = [];
    if (type === 'papers' && pieData) {
        chartData = pieData.map((value, index) => {
            const colorInfo = scoreData.find(item => item.score === (index + 1));
            return { 
                id: index,
                value: value,
                label: `Score ${index + 1}`,
                color: colorInfo ? colorInfo.color : '#FFFFFF'
            };
        });
        console.log(chartData);
    }

    return (
        <Box
            sx={{
                display: 'flex',
                height: '72vh'
            }}
        >
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Tabs
                    orientation="vertical"
                    variant="scrollable"
                    value={value}
                    onChange={handleChange}
                    aria-label="Vertical tabs example"
                    sx={{
                        borderRight: 1,
                        borderColor: 'divider',
                        width: '15vw'
                    }}
                >
                    {data && Object.keys(data).length > 0 &&
                        Object.keys(data).map((key, index) => {
                            return <Tab
                                key={index}
                                label={truncateLabel(key)}
                                sx={{
                                    textTransform: 'none'
                                }}
                                {...a11yProps(index)} />
                        })}
                </Tabs>
                {type === 'papers' &&
                    <Box>
                    <PieChart
                        series={[
                            {
                                data: chartData,
                                valueFormatter: ({ value }) => `${(value * 100).toFixed(1)}%`,
                            },
                        ]}
                        width={250}
                        height={150}
                        slotProps={{
                            legend: { hidden: true },
                        }}
                        sx={{
                            ml: '6vw',
                        }}
                    />
                    </Box>
                }
            </Box>
            <Box>
                {data && Object.keys(data).length > 0 &&
                    Object.keys(data).map((key, index) => {
                        return <TabPanel key={index} value={value} index={index}>
                            {type === 'papers' ? <PapersView query={key} data={data[key]} /> : <DatasetsView query={key} data={data[key]} />}
                        </TabPanel>
                    })
                }
                {data && Object.keys(data).length === 0 && (
                    <Box sx={{ p: 3 }}>
                        <Typography color="text.secondary">No results yet.</Typography>
                    </Box>
                )}
            </Box>
            <Dialog
                open={manualDialogOpen}
                onClose={() => setManualDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Manual PDF Upload Needed</DialogTitle>
                <DialogContent>
                    {uploadError && <Alert severity="error" sx={{ mb: 2 }}>{uploadError}</Alert>}
                    {manualUploadNeeded.length === 0 ? (
                        <Alert severity="success">All required papers are now ready.</Alert>
                    ) : (
                        <Stack spacing={2} sx={{ mt: 1 }}>
                            {manualUploadNeeded.map((paper) => (
                                <Box key={paper.uid} sx={{ border: '1px solid #ddd', borderRadius: 1, p: 2 }}>
                                    <Typography sx={{ fontWeight: 600 }}>{paper.title || 'Untitled paper'}</Typography>
                                    <Typography variant="body2">DOI: {paper.doi || 'N/A'}</Typography>
                                    <Typography variant="body2">Reason: {paper.reason === 'text_too_short' ? `Text too short (${paper.text_chars}/${paper.threshold_chars})` : 'Download failed'}</Typography>
                                    <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: 'center' }}>
                                        <Button component="label" variant="outlined" size="small">
                                            Choose PDF
                                            <input hidden type="file" accept=".pdf,application/pdf" onChange={(e) => handleSelectFile(paper.uid, e)} />
                                        </Button>
                                        <Typography variant="body2">
                                            {selectedFiles[paper.uid]?.name || 'No file selected'}
                                        </Typography>
                                        <Button
                                            variant="contained"
                                            size="small"
                                            onClick={() => handleManualUpload(paper)}
                                            disabled={uploadingUid === paper.uid}
                                        >
                                            {uploadingUid === paper.uid ? 'Uploading...' : 'Upload'}
                                        </Button>
                                    </Stack>
                                </Box>
                            ))}
                        </Stack>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button
                        onClick={() => {
                            sessionStorage.setItem(dismissKey, '1');
                            setManualDialogOpen(false);
                        }}
                    >
                        Close
                    </Button>
                </DialogActions>
            </Dialog>

        </Box>
    );
}
