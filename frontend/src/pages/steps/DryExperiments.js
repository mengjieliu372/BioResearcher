import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import DryExpContent from '../../components/DryExpContent';

// TabPanel组件用于显示选中的Tab内容
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

// a11yProps 提供Tab的可访问性配置
function a11yProps(index) {
    return {
        id: `simple-tab-${index}`,
        'aria-controls': `simple-tabpanel-${index}`,
    };
}


export default function BasicTabs() {
    const [value, setValue] = React.useState(0);
    const [content, setContent] = React.useState(null);

    const handleChange = (event, newValue) => {
        setValue(newValue);
    };

    React.useEffect(() => {
        const dryexp = "dry_experiment" + (value + 1);
        import(`../../data/${dryexp}.json`)
            .then(data => {
                setContent(<DryExpContent data={data.default} />);
            })
            .catch(err => console.error(err));
    }, [value]); // 仅当 value 变化时触发

    return (
        <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
            height: '78vh',
            maxHeight: '78vh',
        }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs
                    value={value}
                    onChange={handleChange}
                    centered
                >
                    <Tab label="Dry Experiment 1" {...a11yProps(0)} sx={{ textTransform: 'none' }} />
                    <Tab label="Dry Experiment 2" {...a11yProps(1)} sx={{ textTransform: 'none' }} />
                    <Tab label="Dry Experiment 3" {...a11yProps(2)} sx={{ textTransform: 'none' }} />
                </Tabs>
            </Box>

            <Box
                sx={{
                    height: '72vh',
                    maxHeight: '70vh',
                    overflowY: 'auto',
                    backgroundColor: '#f5f5f5',
                }}
            >
                <CustomTabPanel value={value} index={0}>
                    {content}
                </CustomTabPanel>
                <CustomTabPanel value={value} index={1}>
                    {content}
                </CustomTabPanel>
                <CustomTabPanel value={value} index={2}>
                    {content}
                </CustomTabPanel>
            </Box>

        </Box>
    );
}