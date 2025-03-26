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
    const { id } = useParams();
    const maxLabelLength = 40;
    const fetchPapersets = async () => {
        try {
            const response = await getPapersets(id);
            setData(response.data);
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

    return (
        <Box
            sx={{ 
                display: 'flex', 
                height: '72vh'
            }}
        >
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
