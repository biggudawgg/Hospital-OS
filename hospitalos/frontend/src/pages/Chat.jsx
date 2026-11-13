// Chat page — full-height AI chat. A question can be passed in the URL: /chat?q=Which ICU beds are free?
import { useSearchParams } from "react-router-dom";
import TopBar from "../components/TopBar";
import ChatPanel from "../components/ChatPanel";

export default function Chat() {
  const [params] = useSearchParams();
  return (
    <div className="flex h-screen flex-col">
      <TopBar title="AI Chat" subtitle="The agent answers by calling MCP tools. It asks before changing any data." />
      <main className="min-h-0 flex-1 p-6">
        <ChatPanel initialQuestion={params.get("q")} />
      </main>
    </div>
  );
}
