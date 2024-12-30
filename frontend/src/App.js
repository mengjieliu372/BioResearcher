import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';  // 确保引入了 Navigate
import AppAppBar from './components/StyledAppBar';

import HomePage from './pages/HomePage';
import NewProject from './pages/NewProject';
import ManageProject from './pages/ManageProject';
import Steps from './components/Steps';
import Search from './pages/steps/Search';
import LiteratureProcessing from './pages/steps/LiteratureProcessing';
import ExperimentalDesign from './pages/steps/ExperimentalDesign';
import DryExperiments from './pages/steps/DryExperiments';
import Programming from './pages/steps/Programming';
import Test from './pages/Test';

function App() {
  return (
    <div className="App">
      <AppAppBar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/new-project" element={<NewProject />} />
        <Route path="/manage-project" element={<ManageProject />} />
        <Route path=":id/steps" element={<Steps />}>
          <Route index element={<Navigate to="search"/>} />
          <Route path="search" element={<Search />} />
          <Route path="literature-processing" element={<LiteratureProcessing />} />
          <Route path="experimental-design" element={<ExperimentalDesign />} />
          <Route path="dry-experiments" element={<DryExperiments />} />
          <Route path="programming" element={<Programming />} />
        </Route>
        <Route path="/test" element={<Test />} />
      </Routes>
    </div>
  );
}

export default App;
