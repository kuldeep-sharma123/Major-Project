"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const ModalTrigger = DialogPrimitive.Trigger;
const ModalPortal = DialogPrimitive.Portal;
const ModalClose = DialogPrimitive.Close;

const ModalOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/70 backdrop-blur-sm",
      "data-[state=open]:animate-in data-[state=closed]:animate-out",
      "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
));
ModalOverlay.displayName = DialogPrimitive.Overlay.displayName;

interface ModalContentProps extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  size?: "sm" | "md" | "lg" | "xl" | "full";
}

const sizeClasses = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
  full: "max-w-[95vw]",
};

const ModalContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  ModalContentProps
>(({ className, children, size = "md", ...props }, ref) => (
  <ModalPortal>
    <ModalOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%]",
        "w-full bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl p-6",
        "data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
        "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
        "data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]",
        "data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]",
        "duration-200",
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-lg p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </ModalPortal>
));
ModalContent.displayName = DialogPrimitive.Content.displayName;

const ModalHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("flex flex-col space-y-1.5 pb-4 border-b border-zinc-800", className)}
    {...props}
  />
);
ModalHeader.displayName = "ModalHeader";

const ModalFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex items-center justify-end gap-3 pt-4 border-t border-zinc-800",
      className
    )}
    {...props}
  />
);
ModalFooter.displayName = "ModalFooter";

const ModalTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold text-zinc-100", className)}
    {...props}
  />
));
ModalTitle.displayName = DialogPrimitive.Title.displayName;

const ModalDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-zinc-400", className)}
    {...props}
  />
));
ModalDescription.displayName = DialogPrimitive.Description.displayName;

const ModalBody = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("py-4", className)} {...props} />
);

export interface ModalProps extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Root> {
  isOpen?: boolean;
  onClose?: () => void;
  title?: string;
  description?: string;
  size?: "sm" | "md" | "lg" | "xl" | "full";
  className?: string;
}

export function Modal({
  isOpen,
  open,
  onClose,
  onOpenChange,
  title,
  description,
  children,
  size = "md",
  className,
  ...props
}: ModalProps) {
  if (isOpen !== undefined || title !== undefined) {
    const isShowing = isOpen !== undefined ? isOpen : (open ?? false);
    const handleOpenChange = (newOpen: boolean) => {
      if (!newOpen) {
        onClose?.();
      }
      onOpenChange?.(newOpen);
    };

    return (
      <DialogPrimitive.Root open={isShowing} onOpenChange={handleOpenChange} {...props}>
        <ModalPortal>
          <ModalOverlay />
          <DialogPrimitive.Content
            className={cn(
              "fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%]",
              "w-full bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl p-6",
              "data-[state=open]:animate-in data-[state=closed]:animate-out",
              "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
              "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
              "data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]",
              "data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]",
              "duration-200",
              sizeClasses[size],
              className
            )}
          >
            {(title || description) && (
              <div className="mb-4">
                {title && (
                  <DialogPrimitive.Title className="text-lg font-semibold text-zinc-100">
                    {title}
                  </DialogPrimitive.Title>
                )}
                {description && (
                  <DialogPrimitive.Description className="text-xs text-zinc-400 mt-1">
                    {description}
                  </DialogPrimitive.Description>
                )}
              </div>
            )}
            {children}
            <DialogPrimitive.Close
              onClick={onClose}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </DialogPrimitive.Close>
          </DialogPrimitive.Content>
        </ModalPortal>
      </DialogPrimitive.Root>
    );
  }

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange} {...props}>
      {children}
    </DialogPrimitive.Root>
  );
}

export {
  ModalTrigger,
  ModalClose,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalTitle,
  ModalDescription,
  ModalBody,
};
