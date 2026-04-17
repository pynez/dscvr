import "@testing-library/jest-dom";

// jsdom doesn't implement HTMLMediaElement — stub it out so audio
// useEffect teardown in TrackScrollCard doesn't produce noise.
window.HTMLMediaElement.prototype.play = () => Promise.resolve();
window.HTMLMediaElement.prototype.pause = () => {};
window.HTMLMediaElement.prototype.load = () => {};
