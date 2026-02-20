"use client";
import { ReactNode, useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  content: string | ReactNode;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
}

export function Tooltip({ content, children, position = "top" }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isVisible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const scrollX = window.scrollX;
      const scrollY = window.scrollY;

      let top = 0;
      let left = 0;

      switch (position) {
        case "top":
          top = rect.top + scrollY - 8; // 8px gap
          left = rect.left + scrollX + rect.width / 2;
          break;
        case "bottom":
          top = rect.bottom + scrollY + 8;
          left = rect.left + scrollX + rect.width / 2;
          break;
        case "left":
          top = rect.top + scrollY + rect.height / 2;
          left = rect.left + scrollX - 8;
          break;
        case "right":
          top = rect.top + scrollY + rect.height / 2;
          left = rect.right + scrollX + 8;
          break;
      }

      setCoords({ top, left });
    }
  }, [isVisible, position]);

  const positionClasses = {
    top: "-translate-x-1/2 -translate-y-full",
    bottom: "-translate-x-1/2",
    left: "-translate-x-full -translate-y-1/2",
    right: "-translate-y-1/2",
  };

  return (
    <>
      <div ref={triggerRef} className="relative inline-block">
        <div
          onMouseEnter={() => setIsVisible(true)}
          onMouseLeave={() => setIsVisible(false)}
          className="cursor-help"
        >
          {children}
        </div>
      </div>
      {isVisible && typeof window !== "undefined" && createPortal(
        <div
          className={`fixed z-[9999] px-3 py-1.5 text-xs leading-relaxed text-white bg-gray-900 rounded-lg shadow-xl max-w-sm pointer-events-none ${positionClasses[position]}`}
          style={{
            top: `${coords.top}px`,
            left: `${coords.left}px`,
            whiteSpace: "normal",
            minWidth: "200px"
          }}
        >
          {content}
          <div
            className={`absolute w-2 h-2 bg-gray-900 transform rotate-45 ${
              position === "top"
                ? "bottom-[-4px] left-1/2 -translate-x-1/2"
                : position === "bottom"
                  ? "top-[-4px] left-1/2 -translate-x-1/2"
                  : position === "left"
                    ? "right-[-4px] top-1/2 -translate-y-1/2"
                    : "left-[-4px] top-1/2 -translate-y-1/2"
            }`}
          />
        </div>,
        document.body
      )}
    </>
  );
}

interface InfoIconProps {
  tooltip: string | ReactNode;
  className?: string;
}

export function InfoIcon({ tooltip, className = "" }: InfoIconProps) {
  return (
    <Tooltip content={tooltip}>
      <span className={`inline-flex items-center justify-center w-4 h-4 text-xs text-gray-500 hover:text-gray-700 ${className}`}>
        ⓘ
      </span>
    </Tooltip>
  );
}
