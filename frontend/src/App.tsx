import SummaryCard from "./components/SummaryCard";

// Example Markdown Content (replace with your actual dynamic content)
const sampleMarkdown = `
# Today's Tech Highlights (Generated May 3, 2025)

Here's a synthesized look at key updates across your subscriptions.

## Major Developments

* **Gemini API Enhanced:** Google rolled out version 1.6 of the Gemini API. Key features include improved fine-tuning capabilities for specialized tasks and significantly larger context windows, enabling more complex interactions. Developers noted the potential for more robust RAG implementations.
* **React 19 Compiler Enters Beta:** The much-anticipated React Compiler is now available in the React 19 Beta. It promises automatic memoization, potentially reducing boilerplate code and improving performance without manual optimization efforts using \`useMemo\` or \`memo\`. Early feedback is positive but points to edge cases needing refinement.
* **Sui Network Throughput Record:** Following a recent network upgrade (v1.21), the Sui blockchain demonstrated sustained high TPS levels in benchmark tests, exceeding previous records. The foundation highlighted improved consensus efficiency as the key factor, aiming to attract large-scale gaming applications.

*
`;

function App() {
  return (
    <div
      className="
      min-h-screen
      flex
      items-center
      justify-center
      p-4 sm:p-8
    "
    >
      <div className="grid grid-cols-4">
        <div className="col-span-1"></div>
        <div className="col-span-2">
          <SummaryCard title="Test" content={sampleMarkdown} />
        </div>
        <div className="col-span-1"></div>
      </div>
    </div>
  );
}

export default App;
