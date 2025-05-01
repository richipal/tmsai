import { Button } from "@/components/ui/button";

interface ExampleQueriesProps {
  examples: string[];
  onSelect: (example: string) => void;
}

export default function ExampleQueries({ examples, onSelect }: ExampleQueriesProps) {
  return (
    <div className="mt-4">
      <h3 className="text-sm font-medium text-gray-500">Try these example queries:</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {examples.map((example, index) => (
          <Button
            key={index}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onSelect(example)}
            className="inline-flex items-center px-3 py-1 text-xs font-medium rounded-md text-primary-700 bg-primary-50 hover:bg-primary-100 border-primary-100"
          >
            {example}
          </Button>
        ))}
      </div>
    </div>
  );
}
