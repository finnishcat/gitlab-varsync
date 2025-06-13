import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { saveAs } from "file-saver";

export default function GitlabVarsyncUI() {
  const [data, setData] = useState([]);
  const [filter, setFilter] = useState("");
  const [license, setLicense] = useState("");

  useEffect(() => {
    fetch("/api/read")
      .then((res) => res.json())
      .then((json) => setData(json));
  }, []);

  const filteredData = data.filter((row) =>
    Object.values(row).some((val) =>
      String(val).toLowerCase().includes(filter.toLowerCase())
    )
  );

  const downloadFile = () => {
    fetch("/api/download")
      .then((res) => res.blob())
      .then((blob) => saveAs(blob, "gitlab_variables_all_groups.xlsx"));
  };

  const fetchLicense = () => {
    fetch("/api/license")
      .then((res) => res.text())
      .then((text) => setLicense(text));
  };

  const executeCommand = (command) => {
    fetch(`/api/${command}`)
      .then((res) => res.json())
      .then((json) => setData(json));
  };

  return (
    <div className="flex h-screen">
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" className="absolute top-4 left-4 z-50">
            <Menu />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64">
          <div className="space-y-4 mt-10">
            <Button onClick={() => executeCommand("read")} className="w-full">
              Read
            </Button>
            <Button onClick={() => executeCommand("write")} className="w-full">
              Write
            </Button>
            <Button onClick={() => executeCommand("update")} className="w-full">
              Update
            </Button>
            <Button onClick={() => executeCommand("search")} className="w-full">
              Search
            </Button>
            <Button onClick={downloadFile} className="w-full">
              Download XLSX
            </Button>
            <Button onClick={fetchLicense} className="w-full">
              License
            </Button>
          </div>
        </SheetContent>
      </Sheet>

      <main className="flex-1 flex flex-col items-center justify-start mt-16 p-6 overflow-auto">
        <div className="mb-4 w-full max-w-4xl mx-auto z-10 relative flex justify-center">
          <Input
            placeholder="Filter table..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full max-w-md"
          />
        </div>

        {license && (
          <Card className="mb-4 w-full max-w-4xl">
            <CardContent>
              <pre className="whitespace-pre-wrap text-sm">{license}</pre>
            </CardContent>
          </Card>
        )}

        <div className="overflow-auto w-full max-w-7xl">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                {data[0] &&
                  Object.keys(data[0]).map((key) => (
                    <th key={key} className="border px-4 py-2 text-left">
                      {key}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody>
              {filteredData.map((row, idx) => (
                <tr
                  key={idx}
                  className={idx % 2 === 0 ? "bg-white" : "bg-gray-50"}
                >
                  {Object.values(row).map((val, i) => (
                    <td key={i} className="border px-4 py-2 text-sm">
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
