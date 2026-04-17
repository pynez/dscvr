import { Routes, Route } from "react-router-dom";
import "./styles/globals.css";

import { Landing }             from "./pages/Landing";
import { Explore }             from "./pages/Explore";
import { Soundtrack }          from "./pages/Soundtrack";
import { BlindTasteTest }      from "./pages/BlindTasteTest";
import { TimeMachine }         from "./pages/TimeMachine";
import { AlgorithmicCapture }  from "./pages/AlgorithmicCapture";
import { Seance }              from "./pages/Seance";

function App() {
  return (
    <Routes>
      <Route path="/"                   element={<Landing />} />
      <Route path="/explore"            element={<Explore />} />
      <Route path="/discover"           element={<Explore />} /> {/* legacy alias */}
      <Route path="/soundtrack"         element={<Soundtrack />} />
      <Route path="/blind-taste-test"   element={<BlindTasteTest />} />
      <Route path="/time-machine"       element={<TimeMachine />} />
      <Route path="/algorithmic-capture" element={<AlgorithmicCapture />} />
      <Route path="/seance"             element={<Seance />} />
    </Routes>
  );
}

export default App;
