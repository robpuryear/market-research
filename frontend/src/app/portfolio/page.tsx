"use client";

import { useState } from "react";
import { PortfolioSummary } from "@/components/portfolio/PortfolioSummary";
import { PositionsTable } from "@/components/portfolio/PositionsTable";
import { AddPositionModal } from "@/components/portfolio/AddPositionModal";
import { SellPositionModal } from "@/components/portfolio/SellPositionModal";
import { usePositions, usePortfolioMetrics } from "@/hooks/usePortfolio";
import type { Position } from "@/lib/types";

export default function PortfolioPage() {
  const { positions, isLoading: positionsLoading, addPosition, sellPosition } = usePositions();
  const { metrics, isLoading: metricsLoading } = usePortfolioMetrics();

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [sellModalOpen, setSellModalOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

  const handleAddPosition = async (data: {
    ticker: string;
    quantity: number;
    price: number;
    date: string;
    notes?: string;
  }) => {
    try {
      await addPosition(data);
      setAddModalOpen(false);
      setSelectedPosition(null);
    } catch (error) {
      console.error("Failed to add position:", error);
      alert("Failed to add position. Please try again.");
    }
  };

  const handleSellPosition = async (data: {
    quantity: number;
    price: number;
    date: string;
    notes?: string;
  }) => {
    if (!selectedPosition) return;

    try {
      await sellPosition(selectedPosition.id, data);
      setSellModalOpen(false);
      setSelectedPosition(null);
    } catch (error) {
      console.error("Failed to sell position:", error);
      alert("Failed to sell position. Please try again.");
    }
  };

  const handleOpenAddModal = (position?: Position) => {
    setSelectedPosition(position || null);
    setAddModalOpen(true);
  };

  const handleOpenSellModal = (position: Position) => {
    setSelectedPosition(position);
    setSellModalOpen(true);
  };

  if (positionsLoading || metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading portfolio...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
          <p className="text-gray-600 mt-1">Track your positions and performance</p>
        </div>
        <button
          onClick={() => handleOpenAddModal()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
        >
          Add Position
        </button>
      </div>

      {/* Portfolio Summary */}
      {metrics && <PortfolioSummary metrics={metrics} />}

      {/* Positions Table */}
      {positions && (
        <PositionsTable
          positions={positions}
          onAddToPosition={handleOpenAddModal}
          onSellPosition={handleOpenSellModal}
        />
      )}

      {/* Add Position Modal */}
      <AddPositionModal
        open={addModalOpen}
        onClose={() => {
          setAddModalOpen(false);
          setSelectedPosition(null);
        }}
        onAdd={handleAddPosition}
        existingPosition={selectedPosition}
      />

      {/* Sell Position Modal */}
      <SellPositionModal
        open={sellModalOpen}
        onClose={() => {
          setSellModalOpen(false);
          setSelectedPosition(null);
        }}
        onSell={handleSellPosition}
        position={selectedPosition}
      />
    </div>
  );
}
