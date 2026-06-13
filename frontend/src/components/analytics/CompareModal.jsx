import { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import CompareAnalytics from '../../pages/CompareAnalytics';

export default function CompareModal() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <button onClick={() => setIsOpen(true)} className="px-4 py-2 bg-gray-200 rounded-full text-sm">Compare Periods</button>
      <Transition appear show={isOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsOpen(false)}>
          <div className="fixed inset-0 bg-black/30" />
          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Dialog.Panel className="w-full max-w-4xl bg-white rounded-2xl shadow-xl p-6">
                <CompareAnalytics />
                <button onClick={() => setIsOpen(false)} className="mt-4 px-4 py-2 bg-gray-200 rounded-full">Close</button>
              </Dialog.Panel>
            </div>
          </div>
        </Dialog>
      </Transition>
    </>
  );
}