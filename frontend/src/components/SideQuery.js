import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { useState, useEffect } from 'react';
import { getPapersets, getDatasets } from '../services/api';
import { useParams } from 'react-router-dom';
import PapersView from './PapersView';
import DatasetsView from './DatasetsView';
import { PieChart } from '@mui/x-charts/PieChart';


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

    const { id } = useParams();
    const maxLabelLength = 40;
    const fetchPapersets = async () => {
        try {
            const response = await getPapersets(id);
            setData(response.data.retrieved_papers);
            setPieData(response.data.count);
        }
        catch (error) {
            console.log(error);
        }
    }

    const fetchDatasets = async () => {
        try {
            const response = await getDatasets(id);
            setData(response.data);
        }
        catch (error) {
            console.log(error);
        }
    }

    useEffect(() => {
        if (type === 'papers') {
            fetchPapersets();
        } else {
            fetchDatasets();
        }
    }, [type])

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

    if (!data) {
        return <Box>Loading...</Box>;
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
                    {data &&
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
                {data &&
                    Object.keys(data).map((key, index) => {
                        return <TabPanel key={index} value={value} index={index}>
                            {type === 'papers' ? <PapersView query={key} data={data[key]} /> : <DatasetsView query={key} data={data[key]} />}
                        </TabPanel>
                    })
                }
            </Box>

        </Box>
    );
}
