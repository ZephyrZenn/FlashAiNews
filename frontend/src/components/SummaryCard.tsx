import { JSX } from "react";
import Markdown from "react-markdown";

interface SummaryCardProps {
  title: string;
  content: string | JSX.Element;
  footer?: string | JSX.Element;
}

const SummaryCard = ({ title, content, footer }: SummaryCardProps) => {
  return (
    <div className="mx-auto w-full h-full">
      {/* Card with layered shadow effect */}
      <div className="relative">
        {/* Bottom shadow layer */}
        <div className="absolute -bottom-2 -right-2 w-full h-full bg-gray-300 rounded-xl"></div>

        {/* Middle shadow layer */}
        <div className="absolute -bottom-1 -right-1 w-full h-full bg-gray-200 rounded-xl"></div>

        {/* Main card */}
        <div className="relative bg-neutral-50 text-gray-900 rounded-xl p-6 shadow-lg border border-gray-100">
          {/* Card title */}
          {title && (
            <div className="mb-4">
              <h3 className="text-xl font-bold">{title}</h3>
              <div className="mt-2 h-px bg-gradient-to-r from-gray-200 via-gray-400 to-gray-200"></div>
            </div>
          )}

          {/* Card content */}
          <div className="mb-4">
            {typeof content === "string" ? (
              <Markdown>{content}</Markdown>
            ) : (
              content
            )}
          </div>

          {/* Card footer */}
          {footer && (
            <div className="mt-6 pt-4 border-t border-gray-100">{footer}</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;
