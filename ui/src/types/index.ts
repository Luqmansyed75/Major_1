export interface User {
  email: string;
  token: string;
}

export interface Thread {
  thread_id: string;
  thread_title: string;
  created_at?: string;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  tools_called?: string[];
}

export interface HITLEvent {
  thread_id: string;
  hitl_event: {
    tool_name: string;
    args: Record<string, any>;
  };
}

export interface IntegrationStatus {
  github_connected: boolean;
  gmail_connected: boolean;
}

export interface AskResponse {
  status: 'done' | 'pending';
  thread_id: string;
  answer?: string;
  hitl_event?: {
    tool_name: string;
    args: Record<string, any>;
  };
  tools_called?: string[];
  error?: string;
}
