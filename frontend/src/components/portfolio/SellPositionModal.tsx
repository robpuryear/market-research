"use client";

import { useState } from "react";
import type { Position } from "@/lib/types";

interface SellPositionModalProps {
  open: boolean;
  onClose: () => void;
  onSell: (data: { quantity: number; price: number; date: string; notes?: string }) => void;
  position: Position | null;
}

export function SellPositionModal({ open, onClose, onSell, position }: SellPositionModalProps) {
  const today = new Date().toISOString().split("T")[0];

  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [date, setDate] = useState(today);
  const [notes, setNotes] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const sellQuantity = parseFloat(quantity);

    if (position && sellQuantity > position.quantity) {
      alert(`Cannot sell ${sellQuantity} shares - only ${position.quantity} owned`);
      return;
    }

    onSell({
      quantity: sellQuantity,
      price: parseFloat(price),
      date,
      notes: notes || undefined,
    });

    // Reset form
    setQuantity("");
    setPrice("");
    setDate(today);
    setNotes("");
    onClose();
  };

  if (!open || !position) return null;

  const sellValue = quantity && price ? parseFloat(quantity) * parseFloat(price) : 0;
  const costBasis = quantity ? parseFloat(quantity) * position.avg_cost_basis : 0;
  const estimatedPnl = sellValue - costBasis;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              Sell {position.ticker}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Position Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Available to Sell</div>
            <div className="text-lg font-bold text-gray-900">
              {position.quantity} shares @ ${position.avg_cost_basis.toFixed(2)} avg
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Quantity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Shares to Sell</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`Max: ${position.quantity}`}
                step="0.001"
                min="0"
                max={position.quantity}
                required
              />
              <div className="flex gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => setQuantity((position.quantity / 2).toString())}
                  className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  50%
                </button>
                <button
                  type="button"
                  onClick={() => setQuantity(position.quantity.toString())}
                  className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  All
                </button>
              </div>
            </div>

            {/* Price */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sell Price per Share ($)</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={position.current_price ? position.current_price.toFixed(2) : "0.00"}
                step="0.01"
                min="0"
                required
              />
            </div>

            {/* Estimated P&L */}
            {quantity && price && (
              <div className="p-3 bg-blue-50 rounded">
                <div className="text-sm text-gray-600 mb-1">Estimated P&L</div>
                <div className={`text-lg font-bold ${estimatedPnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {estimatedPnl >= 0 ? "+" : ""}${estimatedPnl.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Proceeds: ${sellValue.toFixed(2)} - Cost: ${costBasis.toFixed(2)}
                </div>
              </div>
            )}

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sale Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                max={today}
                required
              />
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Exit reason"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium"
              >
                Sell Shares
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
