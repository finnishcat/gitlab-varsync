import React, { useState } from "react";

export function Sheet({ children }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {React.Children.map(children, (child) => {
        // Clone and pass toggle props
        if (child.type.displayName === "SheetTrigger") {
          return React.cloneElement(child, { open, setOpen });
        }
        if (child.type.displayName === "SheetContent") {
          return React.cloneElement(child, { open, setOpen });
        }
        return child;
      })}
    </>
  );
}

export function SheetTrigger({ children, open, setOpen, asChild }) {
  // if asChild, render children directly with onClick
  if (asChild) {
    return React.cloneElement(children, {
      onClick: () => setOpen(!open),
    });
  }
  return (
    <button onClick={() => setOpen(!open)}>{children}</button>
  );
}
SheetTrigger.displayName = "SheetTrigger";

export function SheetContent({ children, side = "left", open, setOpen, className = "" }) {
  return (
    <div
      className={`fixed top-0 ${side}-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-40 ${
        open ? "translate-x-0" : side === "left" ? "-translate-x-full" : "translate-x-full"
      } ${className}`}
    >
      {children}
    </div>
  );
}
SheetContent.displayName = "SheetContent";
