import { useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, ArrowsRightLeftIcon } from '@heroicons/react/24/outline';
import CompareAnalytics from '../../pages/CompareAnalytics';

export default function CompareModal({
  startDate = '',
  endDate = '',
  county = '',
  pathogenCode = '',
  onCompare = null,
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleOpen = () => setIsOpen(true);
  const handleClose = () => setIsOpen(false);

  return (
    <>
      <button
        onClick={handleOpen}
        className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm font-medium text-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <ArrowsRightLeftIcon className="h-4 w-4" />
        Compare Periods
      </button>

      <Transition appear show={isOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={handleClose}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black/50" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-5xl bg-white rounded-2xl shadow-2xl p-6 relative">
                  <div className="flex justify-between items-center mb-4">
                    <Dialog.Title className="text-xl font-semibold text-gray-800">
                      Compare Periods
                    </Dialog.Title>
                    <button
                      onClick={handleClose}
                      className="p-1 rounded-full hover:bg-gray-100 transition-colors"
                    >
                      <XMarkIcon className="h-6 w-6 text-gray-500" />
                    </button>
                  </div>

                  <div className="max-h-[80vh] overflow-y-auto pr-2">
                    <CompareAnalytics
                      startDate={startDate}
                      endDate={endDate}
                      county={county}
                      pathogenCode={pathogenCode}
                      onCompare={onCompare}
                    />
                  </div>

                  <div className="mt-4 flex justify-end border-t pt-4">
                    <button
                      onClick={handleClose}
                      className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-full text-sm font-medium text-gray-700 transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </>
  );
}