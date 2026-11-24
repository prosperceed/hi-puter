"use client";

import { motion, type MotionProps } from "framer-motion";
import type { ReactNode } from "react";

export function MotionReveal({ children, className = "", ...props }: { children: ReactNode; className?: string } & MotionProps) {
  return <motion.div className={className} initial={{ opacity: 0, y: 22 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.2 }} transition={{ duration: 0.55, ease: "easeOut" }} {...props}>{children}</motion.div>;
}
