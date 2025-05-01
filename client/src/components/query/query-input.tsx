import { Search, Mic } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface QueryInputProps {
  value: string;
  onChange: (value: string) => void;
  onExecute: () => void;
  loading?: boolean;
  placeholder?: string;
}

export default function QueryInput({ 
  value, 
  onChange, 
  onExecute, 
  loading = false,
  placeholder = "Ask a question about your data, e.g. 'Show me top 10 customers by order amount'"
}: QueryInputProps) {
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onExecute();
    }
  };
  
  return (
    <div className="flex">
      <div className="relative flex-1 rounded-md shadow-sm">
        <Input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-4 pr-12 py-3 sm:text-sm border-gray-300 rounded-md"
          placeholder={placeholder}
          disabled={loading}
        />
        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
          <Mic className="text-gray-400 hover:text-gray-500 cursor-pointer" />
        </div>
      </div>
      <Button
        type="button"
        onClick={onExecute}
        className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        disabled={loading || !value.trim()}
      >
        {loading ? (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : (
          <Search className="mr-2 h-4 w-4" />
        )}
        Ask
      </Button>
    </div>
  );
}
