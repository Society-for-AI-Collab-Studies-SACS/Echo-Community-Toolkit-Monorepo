import React from 'react'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryPanel } from '../src/panels/MemoryPanel'
import { BundlePanel } from '../src/panels/BundlePanel'

describe('LambdaStateViewer panels scaffold', () => {
  it('renders MemoryPanel empty state', () => {
    render(<MemoryPanel />)
    expect(screen.getByText(/No memory snapshot/i)).toBeTruthy()
  })

  it('renders BundlePanel empty state', () => {
    render(<BundlePanel />)
    expect(screen.getByText(/No bundle loaded/i)).toBeTruthy()
  })
})
