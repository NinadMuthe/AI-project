// frontend/src/services/assistant.ts
import api from "./api";

export interface ChatMessagePayload {
  role: "user" | "assistant";
  content: string;
}

export interface AssistantChatResponse {
  response: string;
  context_used: any;
  source: string;
}

export const sendAssistantMessage = async (
  message: string,
  history: ChatMessagePayload[] = []
): Promise<AssistantChatResponse> => {
  const resp = await api.post<AssistantChatResponse>("/assistant/chat", {
    message,
    history,
  });
  return resp.data;
};
